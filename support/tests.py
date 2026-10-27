import json
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from orders.models import Order
from store.models import Watch

from . import rates
from .models import FAQ, ErrorCode, SupportTicket

User = get_user_model()
REQUIRED_CODES = {400, 401, 403, 404, 429, 500, 503, 470}


def chat(client, message, **extra):
    return client.post("/api/chat/", json.dumps({"message": message, "page": "/test/", **extra}), content_type="application/json")


class SeedDataTests(TestCase):
    def test_at_least_ten_faqs_shown_on_faq_page(self):
        self.assertGreaterEqual(FAQ.objects.filter(is_published=True).count(), 10)
        response = self.client.get("/faq/")
        for faq in FAQ.objects.all():
            self.assertContains(response, faq.question.replace("'", "&#x27;"))

    def test_required_error_codes_exist_and_are_listed(self):
        codes = set(ErrorCode.objects.values_list("code", flat=True))
        self.assertTrue(REQUIRED_CODES <= codes)
        self.assertTrue(ErrorCode.objects.get(code=470).is_site_specific)
        response = self.client.get("/error-codes/")
        for code in REQUIRED_CODES:
            self.assertContains(response, f'id="error-{code}"')


@override_settings(ANTHROPIC_API_KEY="", MONGODB_URI="")
class AssistantTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_explains_error_code(self):
        data = chat(self.client, "What does error 470 mean?").json()
        self.assertEqual(data["source"], "error_code")
        self.assertIn("Watch Already Sold", data["answer"])
        self.assertEqual(chat(self.client, "I got a 429").json()["source"], "error_code")

    def test_answers_from_faq(self):
        data = chat(self.client, "Is it authentic?").json()
        self.assertEqual(data["source"], "faq")
        self.assertIn("Are your watches authentic?", data["answer"])
        self.assertIn("14 days", chat(self.client, "What is the return policy?").json()["answer"])
        self.assertIn("only within India", chat(self.client, "Do you ship internationally?").json()["answer"])

    def test_unknown_question_creates_ticket(self):
        data = chat(self.client, "Can you engrave my initials on a sapphire caseback?", email="asha@example.com").json()
        self.assertEqual(data["source"], "ticket")
        ticket = SupportTicket.objects.get()
        self.assertRegex(ticket.reference, r"^MH-T-\d{5}$")
        self.assertEqual(data["ticket"], ticket.reference)
        self.assertEqual(ticket.email, "asha@example.com")
        self.assertEqual(ticket.page, "/test/")

    def test_small_talk_does_not_create_ticket(self):
        self.assertEqual(chat(self.client, "hello!").json()["source"], "smalltalk")
        self.assertFalse(SupportTicket.objects.exists())

    def test_order_lookup_is_private(self):
        owner = User.objects.create_user("meera", "meera@example.com", "Watch-Lover-2026!")
        watch = Watch.objects.first()
        order = Order.objects.create(
            user=owner, email=owner.email, ship_name="M", ship_phone="9876543210", ship_line1="x", ship_city="Pune",
            ship_state="Maharashtra", ship_pincode="411001", subtotal=watch.price_inr, shipping=0, tax=0, total=watch.price_inr,
        )
        anonymous = chat(self.client, f"Where is my order {order.reference}?").json()
        self.assertEqual(anonymous["source"], "order")
        self.assertIn("/track/", anonymous["answer"])
        self.assertNotIn("Placed", anonymous["answer"])
        self.client.force_login(owner)
        mine = chat(self.client, f"Where is my order {order.reference}?").json()
        self.assertIn("Placed", mine["answer"])

    def test_catalogue_question(self):
        data = chat(self.client, "Is the Rolex Submariner Date 126610LN still available?").json()
        self.assertEqual(data["source"], "catalogue")
        self.assertIn("available", data["answer"])

    def test_bad_json_returns_400(self):
        response = self.client.post("/api/chat/", "not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_chat_is_rate_limited(self):
        for _ in range(20):
            chat(self.client, "hi")
        response = chat(self.client, "hi")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["code"], 429)

    def test_chat_logs_and_feedback_go_to_mongo(self):
        with mock.patch("support.mongo._insert", return_value=True) as insert:
            data = chat(self.client, "Is shipping insured?", session_id="abc").json()
            collection, document = insert.call_args.args
            self.assertEqual(collection, "chat_logs")
            self.assertEqual(document["log_id"], data["log_id"])
            self.assertEqual(document["source"], "faq")
            self.assertEqual(document["session_id"], "abc")

            response = self.client.post(
                "/api/feedback/", json.dumps({"log_id": data["log_id"], "helpful": True, "session_id": "abc"}),
                content_type="application/json",
            )
            self.assertEqual(response.json(), {"ok": True, "stored": True})
            collection, document = insert.call_args.args
            self.assertEqual(collection, "feedback")
            self.assertIs(document["helpful"], True)

    def test_feedback_validation(self):
        response = self.client.post("/api/feedback/", json.dumps({"helpful": "yes"}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_site_works_without_mongo(self):
        # MONGODB_URI is empty: logging is skipped but the answer still comes back.
        self.assertEqual(chat(self.client, "Is it authentic?").status_code, 200)


@override_settings(ANTHROPIC_API_KEY="test-key", MONGODB_URI="")
class ClaudeFallbackTests(TestCase):
    def setUp(self):
        cache.clear()

    def _fake_response(self, text, stop_reason="end_turn"):
        return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])

    @mock.patch("anthropic.Anthropic")
    def test_uses_claude_when_faq_has_no_match(self, client_cls):
        client_cls.return_value.beta.messages.create.return_value = self._fake_response("We can help with that.")
        data = chat(self.client, "Could my grandfather's heirloom be appraised remotely?").json()
        self.assertEqual(data["source"], "ai")
        self.assertEqual(data["answer"], "We can help with that.")
        kwargs = client_cls.return_value.beta.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-opus-5-5")
        self.assertEqual(kwargs["output_config"], {"effort": "low"})
        self.assertEqual(kwargs["fallbacks"], "default")
        self.assertIn("<faqs>", kwargs["system"])
        self.assertEqual(client_cls.call_args.kwargs["timeout"], 15.0)

    @mock.patch("anthropic.Anthropic")
    def test_no_answer_creates_ticket(self, client_cls):
        client_cls.return_value.beta.messages.create.return_value = self._fake_response("NO_ANSWER")
        data = chat(self.client, "Could my grandfather's heirloom be appraised remotely?").json()
        self.assertEqual(data["source"], "ticket")

    @mock.patch("anthropic.Anthropic")
    def test_refusal_creates_ticket(self, client_cls):
        client_cls.return_value.beta.messages.create.return_value = self._fake_response("", stop_reason="refusal")
        self.assertEqual(chat(self.client, "Could my grandfather's heirloom be appraised remotely?").json()["source"], "ticket")


class ErrorPageTests(TestCase):
    def test_custom_404_has_ask_the_assistant(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "This page has stopped ticking.", status_code=404)
        self.assertContains(response, 'data-ask="What does error 404 mean?"', status_code=404)

    def test_custom_500_page(self):
        staff = User.objects.create_user("staff", "staff@example.com", "Watch-Lover-2026!", is_staff=True)
        client = Client(raise_request_exception=False)
        client.force_login(staff)
        response = client.get("/debug/500/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Ask the assistant", status_code=500)

    def test_debug_500_is_staff_only(self):
        self.assertEqual(self.client.get("/debug/500/").status_code, 302)

    def test_missing_csrf_token_returns_403(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post("/api/chat/", json.dumps({"message": "hi"}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        response = client.post("/contact/", {"name": "A", "email": "a@example.com", "subject": "s", "message": "m"})
        self.assertContains(response, "Your session timed out.", status_code=403)


@override_settings(MONGODB_URI="", FX_API_URL="http://127.0.0.1:9/unreachable")
class MonitoringTests(TestCase):
    def setUp(self):
        rates.clear_cache()

    def test_health_json_keys(self):
        response = self.client.get("/health/?format=json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {"status", "uptime_seconds", "checks"})
        self.assertEqual(set(data["checks"]), {"database", "mongodb", "exchange_rates", "anthropic_configured"})
        self.assertEqual(data["checks"]["database"], "ok")
        self.assertEqual(data["checks"]["mongodb"], "not_configured")

    def test_health_returns_503_when_database_down(self):
        with mock.patch("support.views.connection.cursor", side_effect=Exception("db down")):
            response = self.client.get("/health/?format=json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["checks"]["database"], "down")

    def test_rates_fall_back_when_network_call_fails(self):
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            data = self.client.get("/api/rates/").json()
        self.assertEqual(data["source"], "fallback")
        self.assertEqual(data["rates"]["INR"], 1.0)
        self.assertIn("USD", data["rates"])

    def test_rates_live_and_cached(self):
        body = json.dumps({"result": "success", "rates": {"INR": 1, "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "AED": 0.044}})
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = body.encode()
        with mock.patch("urllib.request.urlopen", return_value=fake) as urlopen:
            first = self.client.get("/api/rates/").json()
            self.client.get("/api/rates/")
        self.assertEqual(first["source"], "live")
        self.assertEqual(urlopen.call_count, 1)  # second call served from the 10-minute cache
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 3)

    def test_request_logging_middleware(self):
        with self.assertLogs("maisonheure.requests", level="INFO") as logs:
            self.client.get("/faq/?secret=should-not-be-logged")
        line = logs.output[0]
        self.assertIn("path=/faq/", line)
        self.assertIn("status=200", line)
        self.assertNotIn("should-not-be-logged", line)
