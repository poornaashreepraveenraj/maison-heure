from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from store.models import Watch

from .pricing import compute_totals


class BagTests(TestCase):
    def setUp(self):
        self.watch = Watch.objects.filter(status=Watch.Status.AVAILABLE).first()

    def test_add_available_watch(self):
        response = self.client.post(f"/bag/add/{self.watch.pk}/")
        self.assertRedirects(response, "/bag/")
        self.assertEqual(self.client.session["bag"], [self.watch.pk])
        self.assertContains(self.client.get("/bag/"), self.watch.model)

    def test_add_via_fetch_returns_json_count(self):
        response = self.client.post(f"/bag/add/{self.watch.pk}/", HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(response.json(), {"ok": True, "count": 1, "message": f"{self.watch.title} added to your bag."})

    def test_adding_sold_watch_returns_470(self):
        sold = Watch.objects.filter(status=Watch.Status.SOLD).first()
        response = self.client.post(f"/bag/add/{sold.pk}/")
        self.assertEqual(response.status_code, 470)
        self.assertContains(response, "Someone got there first", status_code=470)
        self.assertContains(response, "Ask the assistant", status_code=470)
        json_response = self.client.post(f"/bag/add/{sold.pk}/", HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(json_response.status_code, 470)
        self.assertEqual(json_response.json()["code"], 470)

    def test_watch_reserved_by_someone_else_returns_470(self):
        self.watch.status = Watch.Status.RESERVED
        self.watch.reserved_by = "user:9999"
        self.watch.reserved_until = timezone.now() + timedelta(minutes=10)
        self.watch.save()
        self.assertEqual(self.client.post(f"/bag/add/{self.watch.pk}/").status_code, 470)

    def test_expired_reservation_is_released(self):
        self.watch.status = Watch.Status.RESERVED
        self.watch.reserved_by = "user:9999"
        self.watch.reserved_until = timezone.now() - timedelta(minutes=1)
        self.watch.save()
        self.assertRedirects(self.client.post(f"/bag/add/{self.watch.pk}/"), "/bag/")
        self.watch.refresh_from_db()
        self.assertEqual(self.watch.status, Watch.Status.AVAILABLE)

    def test_add_requires_post(self):
        self.assertEqual(self.client.get(f"/bag/add/{self.watch.pk}/").status_code, 405)

    def test_promo_code(self):
        self.client.post(f"/bag/add/{self.watch.pk}/")
        self.client.post("/bag/promo/", {"code": "welcome10"})
        totals = self.client.get("/bag/").context["totals"]
        self.assertEqual(totals["promo_code"], "WELCOME10")
        self.assertEqual(totals["discount"], (self.watch.price_inr * Decimal("0.10")).quantize(Decimal("1")))
        self.client.post("/bag/promo/", {"code": "FREEWATCH"})
        self.assertEqual(self.client.get("/bag/").context["totals"]["discount"], 0)


class PricingTests(TestCase):
    def test_totals(self):
        watches = [SimpleNamespace(price_inr=Decimal("1000000"))]
        totals = compute_totals(watches, "WELCOME10", "express")
        self.assertEqual(totals["subtotal"], Decimal("1000000"))
        self.assertEqual(totals["discount"], Decimal("100000"))
        self.assertEqual(totals["shipping"], Decimal("3500"))
        # GST 18% on an assumed 15% dealer margin of the discounted price
        self.assertEqual(totals["tax"], Decimal("24300"))
        self.assertEqual(totals["total"], Decimal("927800"))

    def test_empty_bag_has_no_shipping(self):
        self.assertEqual(compute_totals([])["total"], 0)
