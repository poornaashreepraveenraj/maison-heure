from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Consignment

VALID = {
    "name": "Rohan", "email": "rohan@example.com", "phone": "9876543210", "brand": "Omega", "model": "Seamaster",
    "year": "2015", "condition": "very_good", "box_and_papers": "on", "asking_price": "350000", "photos": "",
}


class ConsignmentTests(TestCase):
    def test_submission_is_saved(self):
        response = self.client.post("/sell/", VALID)
        self.assertRedirects(response, "/sell/")
        consignment = Consignment.objects.get()
        self.assertEqual(consignment.status, Consignment.Status.RECEIVED)
        self.assertTrue(consignment.box_and_papers)

    def test_invalid_year_rejected(self):
        response = self.client.post("/sell/", {**VALID, "year": "3020"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Consignment.objects.exists())

    def test_estimator_values_prefill_form(self):
        response = self.client.get("/sell/?brand=Rolex&year=2019&condition=excellent&papers=1")
        form = response.context["form"]
        self.assertEqual(form.initial["brand"], "Rolex")
        self.assertTrue(form.initial["box_and_papers"])

    def test_submission_appears_on_dashboard(self):
        user = get_user_model().objects.create_user("rohan", "rohan@example.com", "Watch-Lover-2026!")
        self.client.force_login(user)
        self.client.post("/sell/", VALID)
        self.assertContains(self.client.get("/account/"), "Omega Seamaster")
