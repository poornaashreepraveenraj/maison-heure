"""Seed catalogue shared by the data migration and the placeholder-image script.

Plain Python (no Django imports) so scripts/generate_watch_images.py can use it.
`look` only drives the SVG illustration; it is not stored in the database.
Prices are realistic sample values in INR, not live market quotes.
"""

BRANDS = [
    {"name": "Rolex", "slug": "rolex", "country": "Switzerland", "founded": 1905},
    {"name": "Omega", "slug": "omega", "country": "Switzerland", "founded": 1848},
    {"name": "Cartier", "slug": "cartier", "country": "France", "founded": 1847},
    {"name": "Patek Philippe", "slug": "patek-philippe", "country": "Switzerland", "founded": 1839},
    {"name": "Audemars Piguet", "slug": "audemars-piguet", "country": "Switzerland", "founded": 1875},
    {"name": "Tudor", "slug": "tudor", "country": "Switzerland", "founded": 1926},
]

# look: shape (dive | round | chrono | rect | cushion), dial, bezel, case, strap colours
WATCHES = [
    {
        "brand": "rolex", "model": "Submariner Date", "slug": "rolex-submariner-date-126610ln",
        "reference_number": "126610LN", "year": 2022, "case_size_mm": "41.0", "case_material": "Oystersteel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "1350000", "original_retail_inr": "1040000", "status": "available", "featured": True,
        "description": "The definitive dive watch in its current 41 mm form, with the Cerachrom ceramic bezel and calibre 3235. Light desk-diving wear only; bracelet stretch is minimal.",
        "look": {"shape": "dive", "dial": "#0a0d0f", "bezel": "#14181b", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "rolex", "model": "Datejust 41", "slug": "rolex-datejust-41-126334",
        "reference_number": "126334", "year": 2021, "case_size_mm": "41.0", "case_material": "Oystersteel & white gold",
        "movement": "automatic", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "1120000", "original_retail_inr": "1010000", "status": "available", "featured": True,
        "description": "Blue sunburst dial, fluted white-gold bezel and Jubilee bracelet. Serviced and pressure tested; full set with warranty card dated 2021.",
        "look": {"shape": "round", "dial": "#1f3f73", "bezel": "#d9dbdc", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "rolex", "model": "GMT-Master II", "slug": "rolex-gmt-master-ii-126710blro",
        "reference_number": "126710BLRO", "year": 2020, "case_size_mm": "40.0", "case_material": "Oystersteel",
        "movement": "automatic", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "2150000", "original_retail_inr": "1120000", "status": "sold", "featured": False,
        "description": "Red and blue ceramic bezel on the Jubilee bracelet. Light hairlines on the clasp, otherwise very clean.",
        "look": {"shape": "dive", "dial": "#0a0d0f", "bezel": "#b23a3a", "bezel2": "#1f3f73", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "rolex", "model": "Cosmograph Daytona", "slug": "rolex-cosmograph-daytona-116500ln",
        "reference_number": "116500LN", "year": 2019, "case_size_mm": "40.0", "case_material": "Oystersteel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "3800000", "original_retail_inr": "1450000", "status": "available", "featured": True,
        "description": "White 'panda' dial with black Cerachrom tachymeter bezel and calibre 4130. Unpolished case with sharp chamfers.",
        "look": {"shape": "chrono", "dial": "#f2f2f0", "bezel": "#14181b", "case": "#c9ccce", "strap": "#b8bbbe", "sub": "#0a0d0f"},
    },
    {
        "brand": "rolex", "model": "Oyster Perpetual", "slug": "rolex-oyster-perpetual-1002-1978",
        "reference_number": "1002", "year": 1978, "case_size_mm": "34.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "very_good", "style": "vintage", "box_and_papers": False,
        "price_inr": "480000", "original_retail_inr": None, "status": "available", "featured": False,
        "description": "A honest vintage Oyster Perpetual with a silver dial, calibre 1570 and original riveted bracelet. Even patina on the lume plots.",
        "look": {"shape": "round", "dial": "#d8d6cf", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "rolex", "model": "Explorer", "slug": "rolex-explorer-1016-1972",
        "reference_number": "1016", "year": 1972, "case_size_mm": "36.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "good", "style": "vintage", "box_and_papers": False,
        "price_inr": "1450000", "original_retail_inr": None, "status": "available", "featured": False,
        "description": "Gloss-to-matte transitional black dial with 3-6-9 numerals. Case shows honest wear consistent with age; movement freshly serviced.",
        "look": {"shape": "round", "dial": "#121416", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "omega", "model": "Speedmaster Professional Moonwatch", "slug": "omega-speedmaster-moonwatch-310",
        "reference_number": "310.30.42.50.01.001", "year": 2022, "case_size_mm": "42.0", "case_material": "Stainless steel",
        "movement": "manual", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "640000", "original_retail_inr": "700000", "status": "available", "featured": True,
        "description": "Hesalite crystal, step dial and the Master Chronometer calibre 3861. Supplied with the full presentation box and strap kit.",
        "look": {"shape": "chrono", "dial": "#0d0f11", "bezel": "#14181b", "case": "#c9ccce", "strap": "#b8bbbe", "sub": "#22272b"},
    },
    {
        "brand": "omega", "model": "Seamaster Diver 300M", "slug": "omega-seamaster-diver-300m-210",
        "reference_number": "210.30.42.20.03.001", "year": 2021, "case_size_mm": "42.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "420000", "original_retail_inr": "520000", "status": "available", "featured": False,
        "description": "Laser-engraved wave dial in blue ceramic with matching bezel. Helium escape valve at 10 o'clock; light bracelet wear.",
        "look": {"shape": "dive", "dial": "#1d3d6e", "bezel": "#1d3d6e", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "omega", "model": "Constellation Pie-Pan", "slug": "omega-constellation-pie-pan-1968",
        "reference_number": "168.017", "year": 1968, "case_size_mm": "35.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "good", "style": "vintage", "box_and_papers": False,
        "price_inr": "265000", "original_retail_inr": None, "status": "available", "featured": False,
        "description": "Classic pie-pan dial with applied onyx markers and the chronometer calibre 564. Fitted to a new black leather strap.",
        "look": {"shape": "round", "dial": "#e3dfd4", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#2e3438"},
    },
    {
        "brand": "cartier", "model": "Tank Must", "slug": "cartier-tank-must-wsta0041",
        "reference_number": "WSTA0041", "year": 2022, "case_size_mm": "33.7", "case_material": "Stainless steel",
        "movement": "quartz", "condition": "unworn", "style": "dress", "box_and_papers": True,
        "price_inr": "255000", "original_retail_inr": "290000", "status": "available", "featured": True,
        "description": "Large model with silvered dial, Roman numerals and blued-steel hands. Unworn with protective stickers.",
        "look": {"shape": "rect", "dial": "#f4f3ef", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#2e3438"},
    },
    {
        "brand": "cartier", "model": "Santos de Cartier Large", "slug": "cartier-santos-large-wssa0018",
        "reference_number": "WSSA0018", "year": 2020, "case_size_mm": "39.8", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "690000", "original_retail_inr": "760000", "status": "available", "featured": False,
        "description": "Square case with exposed screws and QuickSwitch bracelet; supplied with the additional leather strap.",
        "look": {"shape": "rect", "dial": "#e9e9e6", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "cartier", "model": "Ballon Bleu 36", "slug": "cartier-ballon-bleu-36-w69012z4",
        "reference_number": "W69012Z4", "year": 2017, "case_size_mm": "36.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "very_good", "style": "dress", "box_and_papers": False,
        "price_inr": "340000", "original_retail_inr": "520000", "status": "sold", "featured": False,
        "description": "Guilloché silver dial and the signature cabochon crown guard. Light polishing marks on the bracelet.",
        "look": {"shape": "round", "dial": "#ecebe7", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "patek-philippe", "model": "Calatrava", "slug": "patek-philippe-calatrava-5196r",
        "reference_number": "5196R-001", "year": 2018, "case_size_mm": "37.0", "case_material": "18k rose gold",
        "movement": "manual", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "2850000", "original_retail_inr": "2700000", "status": "available", "featured": False,
        "description": "The essential Calatrava: silvery opaline dial, small seconds and calibre 215 PS. Full set including extract.",
        "look": {"shape": "round", "dial": "#efece4", "bezel": "#d4a58a", "case": "#d4a58a", "strap": "#3b2a22"},
    },
    {
        "brand": "patek-philippe", "model": "Nautilus", "slug": "patek-philippe-nautilus-5711-1a",
        "reference_number": "5711/1A-010", "year": 2019, "case_size_mm": "40.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "11500000", "original_retail_inr": "2800000", "status": "available", "featured": True,
        "description": "Blue-black gradient dial with horizontal embossing. One of the most sought-after steel sports watches; full set, unpolished.",
        "look": {"shape": "cushion", "dial": "#1c2f4f", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "patek-philippe", "model": "Aquanaut", "slug": "patek-philippe-aquanaut-5167a",
        "reference_number": "5167A-001", "year": 2020, "case_size_mm": "40.8", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "7200000", "original_retail_inr": "2400000", "status": "reserved", "featured": False,
        "description": "Black embossed dial on the composite 'tropical' strap. Currently held for a client viewing.",
        "look": {"shape": "cushion", "dial": "#16191b", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#22272b"},
    },
    {
        "brand": "audemars-piguet", "model": "Royal Oak Selfwinding", "slug": "audemars-piguet-royal-oak-15500st",
        "reference_number": "15500ST.OO.1220ST.01", "year": 2021, "case_size_mm": "41.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "6200000", "original_retail_inr": "2600000", "status": "available", "featured": True,
        "description": "Blue 'Grande Tapisserie' dial and integrated bracelet with calibre 4302. Sharp, unpolished finishing.",
        "look": {"shape": "cushion", "dial": "#22406e", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "audemars-piguet", "model": "Royal Oak Offshore Chronograph", "slug": "audemars-piguet-royal-oak-offshore-26470st",
        "reference_number": "26470ST.OO.A104CR.01", "year": 2017, "case_size_mm": "42.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "3400000", "original_retail_inr": "2900000", "status": "available", "featured": False,
        "description": "Grey 'Méga Tapisserie' dial with black rubber-clad pushers and leather strap. Light wear on the bezel edges.",
        "look": {"shape": "chrono", "dial": "#4a4f53", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#22272b", "sub": "#2e3438"},
    },
    {
        "brand": "audemars-piguet", "model": "Code 11.59 Selfwinding", "slug": "audemars-piguet-code-1159-15210bc",
        "reference_number": "15210BC.OO.A002CR.01", "year": 2022, "case_size_mm": "41.0", "case_material": "18k white gold",
        "movement": "automatic", "condition": "unworn", "style": "dress", "box_and_papers": True,
        "price_inr": "2700000", "original_retail_inr": "3100000", "status": "available", "featured": False,
        "description": "Smoked black lacquer dial under a double-curved crystal. Unworn, still in factory protective film.",
        "look": {"shape": "round", "dial": "#0f1113", "bezel": "#e1e2e3", "case": "#e1e2e3", "strap": "#0a0d0f"},
    },
    {
        "brand": "tudor", "model": "Black Bay Fifty-Eight", "slug": "tudor-black-bay-fifty-eight-79030n",
        "reference_number": "79030N", "year": 2021, "case_size_mm": "39.0", "case_material": "Stainless steel",
        "movement": "automatic", "condition": "excellent", "style": "sport", "box_and_papers": True,
        "price_inr": "295000", "original_retail_inr": "340000", "status": "available", "featured": False,
        "description": "Gilt accents, snowflake hands and the in-house MT5402. Riveted-style bracelet with fabric strap included.",
        "look": {"shape": "dive", "dial": "#0d0f11", "bezel": "#14181b", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "tudor", "model": "Pelagos", "slug": "tudor-pelagos-25600tb",
        "reference_number": "25600TB", "year": 2020, "case_size_mm": "42.0", "case_material": "Titanium",
        "movement": "automatic", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "360000", "original_retail_inr": "420000", "status": "sold", "featured": False,
        "description": "Titanium tool diver rated to 500 m, with the self-adjusting spring clasp. Light marks on the bezel.",
        "look": {"shape": "dive", "dial": "#1f3a62", "bezel": "#1f3a62", "case": "#a9adb0", "strap": "#a9adb0"},
    },
]

# Women's and unisex additions (seeded by migration 0005 on existing databases).
WATCHES += [
    {
        "brand": "rolex", "model": "Lady-Datejust 28", "slug": "rolex-lady-datejust-28-279173",
        "reference_number": "279173", "year": 2019, "case_size_mm": "28.0", "case_material": "Oystersteel & yellow gold",
        "movement": "automatic", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "890000", "original_retail_inr": "1150000", "status": "available", "featured": True,
        "description": "Two-tone Rolesor with a silver dial, fluted gold bezel and President-style bracelet. Calibre 2236; light wear on the clasp only.",
        "look": {"shape": "round", "dial": "#e8e2d0", "bezel": "#d9b56a", "case": "#c9ccce", "strap": "#c9ccce"},
    },
    {
        "brand": "rolex", "model": "Datejust 36", "slug": "rolex-datejust-36-126231",
        "reference_number": "126231", "year": 2020, "case_size_mm": "36.0", "case_material": "Oystersteel & Everose gold",
        "movement": "automatic", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "1380000", "original_retail_inr": "1250000", "status": "available", "featured": False,
        "description": "Chocolate dial with diamond hour markers, Everose fluted bezel and Jubilee bracelet — a size that suits any wrist.",
        "look": {"shape": "round", "dial": "#4a2c22", "bezel": "#d4a58a", "case": "#c9ccce", "strap": "#c9ccce"},
    },
    {
        "brand": "cartier", "model": "Tank Louis Cartier Small", "slug": "cartier-tank-louis-small-wgta0010",
        "reference_number": "WGTA0010", "year": 2022, "case_size_mm": "29.5", "case_material": "18k yellow gold",
        "movement": "manual", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "780000", "original_retail_inr": "880000", "status": "available", "featured": True,
        "description": "The classic gold Tank with Roman numerals, sapphire cabochon crown and black alligator strap. Full set with Cartier box.",
        "look": {"shape": "rect", "dial": "#f4f3ef", "bezel": "#d9b56a", "case": "#d9b56a", "strap": "#0a0d0f"},
    },
    {
        "brand": "cartier", "model": "Panthère de Cartier Small", "slug": "cartier-panthere-small-wspn0006",
        "reference_number": "WSPN0006", "year": 2021, "case_size_mm": "30.0", "case_material": "Stainless steel",
        "movement": "quartz", "condition": "very_good", "style": "dress", "box_and_papers": True,
        "price_inr": "360000", "original_retail_inr": "450000", "status": "available", "featured": False,
        "description": "Square case and supple Panthère bracelet that drapes like jewellery. Bracelet sized for a 15.5 cm wrist; extra links included.",
        "look": {"shape": "rect", "dial": "#efede8", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "omega", "model": "Constellation Quartz 28", "slug": "omega-constellation-28-131-10-28",
        "reference_number": "131.10.28.60.55.001", "year": 2020, "case_size_mm": "28.0", "case_material": "Stainless steel",
        "movement": "quartz", "condition": "excellent", "style": "dress", "box_and_papers": True,
        "price_inr": "310000", "original_retail_inr": "420000", "status": "available", "featured": False,
        "description": "Mother-of-pearl dial with diamond indexes and the signature Constellation 'claws'. Battery replaced at inspection.",
        "look": {"shape": "round", "dial": "#f2efe9", "bezel": "#c9ccce", "case": "#c9ccce", "strap": "#b8bbbe"},
    },
    {
        "brand": "patek-philippe", "model": "Twenty~4", "slug": "patek-philippe-twenty-4-4910-1200a",
        "reference_number": "4910/1200A-001", "year": 2018, "case_size_mm": "25.1", "case_material": "Stainless steel, diamond bezel",
        "movement": "quartz", "condition": "very_good", "style": "dress", "box_and_papers": True,
        "price_inr": "1450000", "original_retail_inr": "1300000", "status": "available", "featured": False,
        "description": "Rectangular Twenty~4 with two rows of diamonds on the case and a grey sunburst dial. Serviced by Patek Philippe in 2024.",
        "look": {"shape": "rect", "dial": "#5b6168", "bezel": "#e1e2e3", "case": "#e1e2e3", "strap": "#b8bbbe"},
    },
    {
        "brand": "audemars-piguet", "model": "Royal Oak Lady 33", "slug": "audemars-piguet-royal-oak-lady-67651or",
        "reference_number": "67651OR.ZZ.1261OR.01", "year": 2016, "case_size_mm": "33.0", "case_material": "18k pink gold",
        "movement": "quartz", "condition": "very_good", "style": "sport", "box_and_papers": True,
        "price_inr": "3200000", "original_retail_inr": "3500000", "status": "available", "featured": True,
        "description": "Full pink-gold Royal Oak with a pink 'Grande Tapisserie' dial. Integrated bracelet with light, even wear.",
        "look": {"shape": "cushion", "dial": "#d9b9a0", "bezel": "#d4a58a", "case": "#d4a58a", "strap": "#d4a58a"},
    },
]

# Who each watch is marketed to. Unisex pieces appear under both Men's and Women's.
GENDERS = {
    "rolex-submariner-date-126610ln": "men", "rolex-datejust-41-126334": "men", "rolex-gmt-master-ii-126710blro": "men",
    "rolex-cosmograph-daytona-116500ln": "men", "rolex-oyster-perpetual-1002-1978": "unisex", "rolex-explorer-1016-1972": "unisex",
    "omega-speedmaster-moonwatch-310": "men", "omega-seamaster-diver-300m-210": "men", "omega-constellation-pie-pan-1968": "unisex",
    "cartier-tank-must-wsta0041": "unisex", "cartier-santos-large-wssa0018": "men", "cartier-ballon-bleu-36-w69012z4": "unisex",
    "patek-philippe-calatrava-5196r": "unisex", "patek-philippe-nautilus-5711-1a": "men", "patek-philippe-aquanaut-5167a": "men",
    "audemars-piguet-royal-oak-15500st": "men", "audemars-piguet-royal-oak-offshore-26470st": "men",
    "audemars-piguet-code-1159-15210bc": "men", "tudor-black-bay-fifty-eight-79030n": "unisex", "tudor-pelagos-25600tb": "men",
    "rolex-lady-datejust-28-279173": "women", "rolex-datejust-36-126231": "unisex", "cartier-tank-louis-small-wgta0010": "women",
    "cartier-panthere-small-wspn0006": "women", "omega-constellation-28-131-10-28": "women",
    "patek-philippe-twenty-4-4910-1200a": "women", "audemars-piguet-royal-oak-lady-67651or": "women",
}
for _watch in WATCHES:
    _watch["gender"] = GENDERS.get(_watch["slug"], "unisex")

IMAGE_VIEWS = [
    ("front", "front view"),
    ("angle", "angled view"),
    ("back", "caseback view"),
    ("side", "side profile"),
]
