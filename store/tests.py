from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import Brand, Watch
from .templatetags.store_extras import format_inr


@override_settings(FX_API_URL="http://127.0.0.1:9/unreachable")
class PublicPagesTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_all_public_pages_return_200(self):
        watch = Watch.objects.first()
        urls = [
            "/", "/shop/", watch.get_absolute_url(), "/bag/", "/track/", "/sell/", "/about/",
            "/faq/", "/error-codes/", "/contact/", "/register/", "/login/", "/health/",
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # The chat widget must be on every page.
                self.assertContains(response, "Maison Heure Concierge")

    def test_landing_page_content(self):
        response = self.client.get("/")
        self.assertContains(response, "Pre-Loved.")
        self.assertContains(response, 'data-tabs')
        self.assertContains(response, "What's my watch worth?")


class CatalogueTests(TestCase):
    def test_seed_data(self):
        self.assertEqual(Brand.objects.count(), 6)
        self.assertGreaterEqual(Watch.objects.count(), 16)
        self.assertTrue(Watch.objects.filter(status=Watch.Status.SOLD).exists())
        self.assertTrue(Watch.objects.filter(status=Watch.Status.AVAILABLE).exists())
        prices = Watch.objects.values_list("price_inr", flat=True)
        self.assertGreaterEqual(min(prices), 250000)
        self.assertLessEqual(max(prices), 12000000)
        for watch in Watch.objects.all():
            self.assertGreaterEqual(watch.images.count(), 1)

    def test_unsplash_photos_and_listing_updates(self):
        sub = Watch.objects.visible().get(slug="rolex-submariner-date-126610ln")
        self.assertTrue(sub.primary_image.url.startswith("https://images.unsplash.com/"))
        self.assertEqual(sub.primary_image.credit, "Patrick Langwallner on Unsplash")
        self.assertTrue(sub.primary_image.is_photo)
        self.assertEqual(Watch.objects.filter(images__external_url__startswith="https://images.unsplash.com/").distinct().count(), 17)
        page = self.client.get(sub.get_absolute_url())
        self.assertContains(page, "Patrick Langwallner on Unsplash")
        self.assertContains(page, "has-photo")
        # Listings adjusted to match their photos
        self.assertEqual(Watch.objects.get(slug="rolex-oyster-perpetual-36-126000").reference_number, "126000")
        self.assertIn("Mint-green", Watch.objects.get(slug="rolex-datejust-41-126334").description)
        self.assertTrue(Watch.objects.get(slug="audemars-piguet-royal-oak-15500st").reference_number.endswith(".03"))
        # Only watches with real photos remain in the catalogue
        self.assertEqual(Watch.objects.count(), 17)
        self.assertFalse(Watch.objects.filter(slug="rolex-gmt-master-ii-126710blro").exists())
        for watch in Watch.objects.visible():
            self.assertTrue(watch.primary_image.is_photo, watch.slug)

    def test_live_status_endpoint(self):
        watch = Watch.objects.filter(status=Watch.Status.AVAILABLE).first()
        data = self.client.get(f"/api/watches/{watch.slug}/status/").json()
        self.assertEqual(data, {"slug": watch.slug, "status": "available", "is_available": True})
        Watch.objects.filter(pk=watch.pk).update(status=Watch.Status.SOLD)
        self.assertFalse(self.client.get(f"/api/watches/{watch.slug}/status/").json()["is_available"])
        self.assertEqual(self.client.get("/api/watches/no-such-watch/status/").status_code, 404)

    def test_shop_partial_reports_total_for_live_updates(self):
        partial = self.client.get("/shop/?gender=women&partial=1")
        self.assertContains(partial, 'data-total="8"')
        self.assertContains(partial, "Women&#x27;s watches")

    def test_shop_filters_by_brand_and_search(self):
        response = self.client.get("/shop/?brand=omega")
        brands = {w.brand.slug for w in response.context["page"].object_list}
        self.assertEqual(brands, {"omega"})
        response = self.client.get("/shop/?q=126610LN")
        self.assertEqual(response.context["total"], 1)

    def test_every_watch_has_a_gender_and_all_three_exist(self):
        counts = {g: Watch.objects.filter(gender=g).count() for g in Watch.Gender.values}
        self.assertTrue(all(counts.values()), counts)

    def test_gender_filter_includes_unisex_in_mens_and_womens(self):
        def genders(url):
            return {w.gender for w in self.client.get(url).context["page"].paginator.object_list}

        self.assertEqual(genders("/shop/?gender=women"), {"women", "unisex"})
        self.assertEqual(genders("/shop/?gender=men"), {"men", "unisex"})
        self.assertEqual(genders("/shop/?gender=unisex"), {"unisex"})
        self.assertContains(self.client.get("/shop/?gender=women"), "Women&#x27;s watches")
        data = self.client.get("/api/watches/?gender=women&limit=24").json()
        self.assertTrue(all(item["gender"] in {"women", "unisex"} for item in data["results"]))

    def test_shop_sort_and_pagination_partial(self):
        response = self.client.get("/shop/?sort=price_asc")
        prices = [w.price_inr for w in response.context["page"].object_list]
        self.assertEqual(prices, sorted(prices))
        partial = self.client.get("/shop/?page=2&partial=1")
        self.assertEqual(partial.status_code, 200)
        self.assertNotContains(partial, "<html")

    def test_api_watches_filters_by_brand(self):
        data = self.client.get("/api/watches/?brand=cartier").json()
        self.assertGreater(data["count"], 0)
        self.assertTrue(all(item["brand"] == "Cartier" for item in data["results"]))
        self.assertIn("html", data)

    def test_unknown_watch_is_404(self):
        self.assertEqual(self.client.get("/watch/not-a-real-watch/").status_code, 404)

    def test_photo_url_overrides_placeholder(self):
        watch = Watch.objects.first()
        watch.images.create(external_url="https://images.example.com/sub.jpg", alt="Photo", order=0)
        watch = Watch.objects.visible().get(pk=watch.pk)
        self.assertEqual(watch.primary_image.url, "https://images.example.com/sub.jpg")
        self.assertContains(self.client.get(watch.get_absolute_url()), "https://images.example.com/sub.jpg")

    def test_cards_offer_quick_add_only_for_available_watches(self):
        response = self.client.get("/shop/?available=1")
        self.assertContains(response, 'class="quick-add"')
        sold = self.client.get("/api/watches/?brand=tudor").json()["html"]
        self.assertIn("Sold", sold)

    def test_indian_number_format(self):
        self.assertEqual(format_inr(1234567), "₹12,34,567")
        self.assertEqual(format_inr("250000.00"), "₹2,50,000")
        self.assertEqual(format_inr(999), "₹999")
