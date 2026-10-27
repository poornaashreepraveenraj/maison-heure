import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase

from cart.pricing import compute_totals
from store.models import Watch

from .models import Order

User = get_user_model()
PASSWORD = "Watch-Lover-2026!"
SHIPPING = {
    "name": "Asha Rao", "email": "asha@example.com", "phone": "9876543210", "line1": "12 Marine Drive",
    "line2": "", "city": "Mumbai", "state": "Maharashtra", "pincode": "400002",
}


class CheckoutFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.watch = Watch.objects.filter(status=Watch.Status.AVAILABLE).order_by("price_inr").first()

    def test_checkout_requires_login(self):
        response = self.client.get("/checkout/")
        self.assertRedirects(response, "/login/?next=/checkout/")

    def test_register_login_checkout_creates_order_and_marks_sold(self):
        # Register (auto-login), log out, then log in again via the login form.
        response = self.client.post(
            "/register/", {"username": "asha", "email": "asha@example.com", "password1": PASSWORD, "password2": PASSWORD}
        )
        self.assertRedirects(response, "/account/")
        self.client.post("/logout/")
        response = self.client.post("/login/", {"username": "asha", "password": PASSWORD})
        self.assertRedirects(response, "/account/")

        self.client.post(f"/bag/add/{self.watch.pk}/")
        self.assertEqual(self.client.get("/checkout/").status_code, 200)
        self.watch.refresh_from_db()
        self.assertEqual(self.watch.status, Watch.Status.RESERVED)  # 15-minute hold

        self.assertRedirects(self.client.post("/checkout/", {**SHIPPING, "save_address": "on"}), "/checkout/delivery/")
        self.assertRedirects(self.client.post("/checkout/delivery/", {"delivery": "express"}), "/checkout/payment/")

        # A failed demo payment creates nothing.
        self.assertRedirects(self.client.post("/checkout/payment/", {"outcome": "fail"}), "/checkout/payment/")
        self.assertFalse(Order.objects.exists())

        # The confirmation email is sent on transaction commit.
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/checkout/payment/", {"outcome": "success"})
        order = Order.objects.get()
        self.assertRedirects(response, f"/orders/{order.reference}/confirmed/")
        self.assertRegex(order.reference, r"^MH-\d{4}-\d{6}$")
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.items.get().watch, self.watch)
        self.assertEqual(order.total, compute_totals([self.watch], "", "express")["total"])
        self.assertEqual(order.events.count(), 1)
        self.watch.refresh_from_db()
        self.assertEqual(self.watch.status, Watch.Status.SOLD)
        self.assertEqual(self.client.session.get("bag"), [])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.reference, mail.outbox[0].subject)
        self.assertEqual(order.user.addresses.count(), 1)

        self.assertContains(self.client.get(f"/orders/{order.reference}/confirmed/"), order.reference)
        self.assertContains(self.client.get("/account/orders/"), order.reference)

    def test_checkout_of_watch_sold_meanwhile_returns_470(self):
        user = User.objects.create_user("ravi", "ravi@example.com", PASSWORD)
        self.client.force_login(user)
        self.client.post(f"/bag/add/{self.watch.pk}/")
        Watch.objects.filter(pk=self.watch.pk).update(status=Watch.Status.SOLD)
        self.assertEqual(self.client.get("/checkout/").status_code, 470)

    def test_invalid_pincode_rejected(self):
        user = User.objects.create_user("ravi", "ravi@example.com", PASSWORD)
        self.client.force_login(user)
        self.client.post(f"/bag/add/{self.watch.pk}/")
        response = self.client.post("/checkout/", {**SHIPPING, "pincode": "01234"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("pincode", response.context["form"].errors)


class TrackingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user("meera", "meera@example.com", PASSWORD)
        watch = Watch.objects.filter(status=Watch.Status.AVAILABLE).first()
        self.order = Order.objects.create(
            user=self.owner, email="meera@example.com", ship_name="Meera", ship_phone="9876543210",
            ship_line1="1 MG Road", ship_city="Pune", ship_state="Maharashtra", ship_pincode="411001",
            subtotal=watch.price_inr, shipping=1500, tax=0, total=watch.price_inr + 1500,
        )
        self.order.items.create(watch=watch, price_at_purchase=watch.price_inr)
        self.order.events.create(status=Order.Status.PLACED)

    def test_lookup_with_wrong_email_fails(self):
        response = self.client.post("/track/", {"reference": self.order.reference, "email": "someone@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "couldn&#x27;t find an order")

    def test_lookup_with_matching_email_shows_timeline(self):
        response = self.client.post("/track/", {"reference": self.order.reference.lower(), "email": "MEERA@example.com"}, follow=True)
        self.assertContains(response, "Timeline")
        self.assertContains(response, "Out for delivery")

    def test_repeated_failed_lookups_return_429(self):
        for _ in range(5):
            self.client.post("/track/", {"reference": "MH-2026-999999", "email": "x@example.com"})
        response = self.client.post("/track/", {"reference": "MH-2026-999999", "email": "x@example.com"})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Ask the assistant", status_code=429)

    def test_other_users_cannot_view_order(self):
        intruder = User.objects.create_user("kabir", "kabir@example.com", PASSWORD)
        self.client.force_login(intruder)
        self.assertEqual(self.client.get(f"/orders/{self.order.reference}/").status_code, 403)
        self.assertEqual(self.client.get(f"/orders/{self.order.reference}/confirmed/").status_code, 403)

    def test_anonymous_order_page_redirects_to_lookup(self):
        response = self.client.get(f"/orders/{self.order.reference}/")
        self.assertRedirects(response, f"/track/?ref={self.order.reference}")

    def test_status_change_appends_timeline_event(self):
        self.order.set_status(Order.Status.SHIPPED, "Handed to courier")
        self.client.force_login(self.owner)
        timeline = self.client.get(f"/orders/{self.order.reference}/").context["timeline"]
        done = [step["status"] for step in timeline if step["done"]]
        self.assertEqual(done, ["placed", "authenticated", "packed", "shipped"])
        self.assertIsNotNone(next(s for s in timeline if s["status"] == "shipped")["at"])


class AdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", PASSWORD)
        self.client.force_login(self.admin)

    def test_admin_changelists_load(self):
        for url in ["/admin/", "/admin/store/watch/", "/admin/orders/order/", "/admin/support/supportticket/",
                    "/admin/support/faq/", "/admin/support/errorcode/", "/admin/sell/consignment/"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
        self.assertContains(self.client.get("/admin/"), "Maison Heure Admin")

    def test_mark_shipped_action_adds_event(self):
        watch = Watch.objects.first()
        order = Order.objects.create(
            email="a@example.com", ship_name="A", ship_phone="9876543210", ship_line1="x", ship_city="y",
            ship_state="Goa", ship_pincode="403001", subtotal=watch.price_inr, shipping=0, tax=0, total=watch.price_inr,
        )
        self.client.post("/admin/orders/order/", {"action": "mark_shipped", "_selected_action": [order.pk]})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertTrue(order.events.filter(status="shipped").exists())
        self.assertTrue(re.match(r"^MH-\d{4}-\d{6}$", order.reference))
