"""Swap the placeholder illustrations for real photos on 17 watches.

All photos are free to use under the Unsplash License (https://unsplash.com/license)
and are served from Unsplash's CDN. Credits are stored on each image and listed in
the README. Three listings are adjusted so the description matches the photo:
Datejust 41 (mint-green dial), Oyster Perpetual (modern 36 mm, blue dial) and
Royal Oak 15500ST (black dial).
"""
from decimal import Decimal

from django.db import migrations

CDN = "https://images.unsplash.com/{}?w=1000&h=1000&fit=crop&q=80&auto=format"

# watch slug -> [(photo id, alt text, photographer, Unsplash page), ...]; first photo is the main one.
PHOTOS = {
    "rolex-submariner-date-126610ln": [
        ("photo-1662384197911-e82189f4dc60", "Rolex Submariner Date with black dial on a light background", "Patrick Langwallner", "a-black-watch-on-a-white-surface-GaHmbqNh5q8"),
        ("photo-1662384201132-c181be518cd2", "Rolex Submariner Date bracelet and bezel on a blue surface", "Patrick Langwallner", "a-watch-on-a-blue-surface-Sik80UHsb1Y"),
    ],
    "rolex-datejust-41-126334": [
        ("photo-1766595898967-22c61e0be796", "Rolex Datejust 41 with mint-green dial on the wrist", "Damian Kamp", "man-wearing-a-luxury-wristwatch-on-his-arm-miLQOt3_sMQ"),
    ],
    "rolex-cosmograph-daytona-116500ln": [
        ("photo-1657104996708-044ef9812f85", "Rolex Cosmograph Daytona with white dial against a cloudy sky", "Cash Macanaya", "a-watch-with-a-cloudy-sky-5enLV7bg6iw"),
    ],
    "rolex-explorer-1016-1972": [
        ("photo-1587836374828-4dbafa94cf0e", "Rolex Explorer with black dial, close-up", "Carlos Esteves", "silver-and-black-round-analog-watch-Ae3OHpJfngc"),
        ("photo-1782012133180-91aca4bcf9ad", "Rolex Explorer worn on the wrist with a light blue shirt", "Soban Ahmed", "wrist-wearing-a-silver-watch-on-a-light-blue-shirt-wEtMI-MSDCU"),
    ],
    "rolex-oyster-perpetual-1002-1978": [
        ("photo-1760541791863-424a4af5de1c", "Rolex Oyster Perpetual with blue dial in its green presentation box", "Ali Ccu", "rolex-watch-with-blue-dial-in-green-box-dQT79SjiO1g"),
    ],
    "omega-speedmaster-moonwatch-310": [
        ("photo-1588866681220-a46150c5eb23", "Omega Speedmaster Moonwatch on a light background", "Hans Gaber", "black-and-silver-round-analog-watch-x-BEn77CZ8Q"),
        ("photo-1588524789663-e6163803c589", "Omega Speedmaster Moonwatch dial and bracelet, close-up", "Hans Gaber", "silver-and-black-round-analog-watch-idSBXY2QWOE"),
    ],
    "omega-seamaster-diver-300m-210": [
        ("photo-1774744287122-4a0c96786dbd", "Omega Seamaster with blue wave dial and blue bezel", "John Torcasio", "a-close-up-of-a-luxury-stainless-steel-watch-_teOJRLWe0o"),
    ],
    "omega-constellation-pie-pan-1968": [
        ("photo-1677445166019-4fa91a090e49", "Vintage Omega Constellation on a brown leather strap", "Francesco Dondi", "a-watch-sitting-on-top-of-a-brown-case-X-cRJrqFzHA"),
    ],
    "cartier-tank-louis-small-wgta0010": [
        ("photo-1581063683670-6df2247f1d8e", "Gold Cartier Tank on a black strap in its red presentation box", "Studio Crevettes", "gold-and-black-analog-watch-in-box-Ju-6TPKXdBs"),
    ],
    "cartier-santos-large-wssa0018": [
        ("photo-1687040481503-3595ef7b5672", "Steel Cartier Santos on a dark background", "Keyur Jadav", "a-close-up-of-a-wrist-watch-on-a-table-OneGplJm4ko"),
    ],
    "patek-philippe-nautilus-5711-1a": [
        ("photo-1626624386327-5204714bae9f", "Patek Philippe Nautilus with blue dial", "Diniy Salleh", "silver-and-blue-analog-watch-gaBYtKLzf-I"),
        ("photo-1626624386394-4d1fb329e0d8", "Patek Philippe Nautilus sapphire caseback and bracelet", "Diniy Salleh", "silver-and-black-digital-watch-cDQi-wnmE88"),
    ],
    "audemars-piguet-royal-oak-15500st": [
        ("photo-1695921504311-a42b163ae0a3", "Audemars Piguet Royal Oak black tapisserie dial, close-up", "Ahsan Khan", "a-close-up-of-a-watch-on-a-table-XDTnKDj9yCg"),
    ],
    "audemars-piguet-royal-oak-lady-67651or": [
        ("photo-1638872726305-35e2e39fb154", "Rose-gold Audemars Piguet Royal Oak on a dark surface", "m G", "a-wooden-watch-sitting-on-top-of-a-black-surface-FeiPAKIvSvg"),
    ],
    "tudor-black-bay-fifty-eight-79030n": [
        ("photo-1647174317920-a9c6780f825b", "Tudor Black Bay Fifty-Eight with gilt details on a black surface", "Fidel Fernando", "a-watch-sitting-on-a-black-surface-with-gold-numbers-3K0LfPFBz9U"),
        ("photo-1661086381638-f973ca589bb8", "Tudor Black Bay on a fabric strap resting on a rock", "Horology Hands", "a-watch-on-a-rock-ecOiTQFt9ho"),
    ],
    "tudor-pelagos-25600tb": [
        ("photo-1697809510926-4c11d0820dba", "Tudor Pelagos with blue dial on a dark table", "Joshua katt", "a-watch-sitting-on-top-of-a-black-table-Y7ztFMKsfV8"),
        ("photo-1697809653305-aa9799a495c2", "Tudor Pelagos blue dial and bezel, close-up", "Joshua katt", "a-blue-and-white-watch-sitting-on-top-of-a-bed-dOQelfcqwWA"),
    ],
    "rolex-lady-datejust-28-279173": [
        ("photo-1620625515032-6ed0c1790c75", "Two-tone Rolex Lady-Datejust with silver dial on a wooden table", "Yash Parashar", "silver-and-white-round-analog-watch-LWPPpkn6NEQ"),
        ("photo-1619976396248-56d05beb2919", "Two-tone Rolex Lady-Datejust bracelet, side view", "Yash Parashar", "silver-link-bracelet-round-analog-watch-VfozQD-IgdA"),
    ],
    "rolex-datejust-36-126231": [
        ("photo-1600003014755-ba31aa59c4b6", "Two-tone Rolex Datejust 36 with chocolate diamond dial", "Laurenz Heymann", "silver-and-gold-round-analog-watch-at-10-10-al6s6JpnZis"),
        ("photo-1773414685933-bfc3ccf89a3c", "Two-tone Rolex Datejust 36 dial and Jubilee bracelet, close-up", "Phước Sang", "a-close-up-of-a-two-tone-rolex-watch-with-diamonds-8PzBx71aecg"),
    ],
}

# Listing changes so the text matches the photo.
LISTING_UPDATES = {
    "rolex-datejust-41-126334": {
        "description": "Mint-green sunburst dial, fluted white-gold bezel and Jubilee bracelet. Serviced and pressure tested; full set with warranty card dated 2021.",
    },
    "rolex-oyster-perpetual-1002-1978": {
        "slug": "rolex-oyster-perpetual-36-126000",
        "model": "Oyster Perpetual 36",
        "reference_number": "126000",
        "year": 2021,
        "case_size_mm": Decimal("36.0"),
        "case_material": "Oystersteel",
        "condition": "excellent",
        "style": "dress",
        "box_and_papers": True,
        "price_inr": Decimal("790000"),
        "original_retail_inr": Decimal("640000"),
        "description": "Bright blue dial, Oystersteel case and Oyster bracelet with calibre 3230. Full set in its green Rolex box, as pictured.",
    },
    "audemars-piguet-royal-oak-15500st": {
        "reference_number": "15500ST.OO.1220ST.03",
        "description": "Black 'Grande Tapisserie' dial and integrated bracelet with calibre 4302. Sharp, unpolished finishing.",
    },
}


def apply_photos(apps, schema_editor):
    Watch = apps.get_model("store", "Watch")
    WatchImage = apps.get_model("store", "WatchImage")

    for slug, photos in PHOTOS.items():
        watch = Watch.objects.filter(slug=slug).first()
        if watch is None:
            continue
        watch.images.all().delete()  # photos replace the illustrations entirely
        WatchImage.objects.bulk_create(
            [
                WatchImage(
                    watch=watch,
                    external_url=CDN.format(photo_id),
                    alt=alt,
                    credit=f"{photographer} on Unsplash",
                    credit_url=f"https://unsplash.com/photos/{page}",
                    order=index,
                )
                for index, (photo_id, alt, photographer, page) in enumerate(photos, start=1)
            ]
        )

    for slug, changes in LISTING_UPDATES.items():
        Watch.objects.filter(slug=slug).update(**changes)


class Migration(migrations.Migration):
    dependencies = [("store", "0006_watchimage_credit")]
    operations = [migrations.RunPython(apply_photos, migrations.RunPython.noop)]
