from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from store.models import Watch, Wishlist

User = get_user_model()
PASSWORD = "Watch-Lover-2026!"


class AccountTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_dashboard_and_wishlist_require_login(self):
        self.assertRedirects(self.client.get("/account/"), "/login/?next=/account/")
        self.assertRedirects(self.client.get("/account/wishlist/"), "/login/?next=/account/wishlist/")

    def test_register_logs_in_and_shows_dashboard(self):
        response = self.client.post(
            "/register/", {"username": "kabir", "email": "kabir@example.com", "password1": PASSWORD, "password2": PASSWORD}, follow=True
        )
        self.assertContains(response, "Welcome, kabir")

    def test_duplicate_email_rejected(self):
        User.objects.create_user("first", "same@example.com", PASSWORD)
        response = self.client.post(
            "/register/", {"username": "second", "email": "same@example.com", "password1": PASSWORD, "password2": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)

    def test_login_redirects_to_next_and_logout_is_post_only(self):
        User.objects.create_user("ana", "ana@example.com", PASSWORD)
        response = self.client.post("/login/?next=/account/wishlist/", {"username": "ana", "password": PASSWORD, "next": "/account/wishlist/"})
        self.assertRedirects(response, "/account/wishlist/")
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.assertRedirects(self.client.post("/logout/"), "/")

    def test_open_redirect_is_blocked(self):
        response = self.client.post(
            "/register/",
            {"username": "eve", "email": "eve@example.com", "password1": PASSWORD, "password2": PASSWORD, "next": "https://evil.example/"},
        )
        self.assertRedirects(response, "/account/")

    def test_repeated_failed_logins_return_429(self):
        for _ in range(8):
            self.client.post("/login/", {"username": "nobody", "password": "wrong"})
        response = self.client.post("/login/", {"username": "nobody", "password": "wrong"})
        self.assertEqual(response.status_code, 429)

    def test_register_race_shows_form_error_not_500(self):
        """A double-submitted sign-up whose second insert hits the unique constraint."""
        from django.db import IntegrityError
        from unittest import mock

        with mock.patch("accounts.forms.RegisterForm.save", side_effect=IntegrityError("UNIQUE constraint failed")):
            response = self.client.post(
                "/register/?next=/checkout/",
                {"username": "poorna", "email": "p@example.com", "password1": PASSWORD, "password2": PASSWORD, "next": "/checkout/"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please sign in instead")

    def test_register_from_checkout_returns_to_checkout_with_bag(self):
        watch = Watch.objects.filter(status=Watch.Status.AVAILABLE).first()
        self.client.post(f"/bag/add/{watch.pk}/")
        response = self.client.post(
            "/register/?next=/checkout/",
            {"username": "poorna", "email": "p@example.com", "password1": PASSWORD, "password2": PASSWORD, "next": "/checkout/"},
        )
        self.assertRedirects(response, "/checkout/")
        self.assertContains(self.client.get("/checkout/"), watch.model)

    def test_passwords_use_scrypt(self):
        user = User.objects.create_user("hash", "hash@example.com", PASSWORD)
        self.assertTrue(user.password.startswith("scrypt$"))

    def test_favicon_redirect(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].endswith("img/favicon.svg"))

    def test_wishlist_toggle(self):
        user = User.objects.create_user("ana", "ana@example.com", PASSWORD)
        watch = Watch.objects.first()
        url = f"/account/wishlist/toggle/{watch.pk}/"
        self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").status_code, 401)
        self.client.force_login(user)
        self.assertTrue(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json()["in_wishlist"])
        self.assertContains(self.client.get("/account/wishlist/"), watch.model)
        self.assertFalse(self.client.post(url, HTTP_X_REQUESTED_WITH="fetch").json()["in_wishlist"])
        self.assertFalse(Wishlist.objects.exists())
