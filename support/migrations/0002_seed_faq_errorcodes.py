"""Seed 15 FAQs and 9 error codes (the 8 required ones plus 405).

The assistant answers from exactly this data, so editing it in /admin/
changes what the assistant says.
"""
from django.db import migrations

FAQS = [
    ("Authenticity", "Are your watches authentic?",
     "Yes. Every watch is 100% authentic and is inspected by our in-house watchmakers before it is listed. Each one ships with a Maison Heure certificate of authenticity, and if a watch is ever proven not to be genuine we refund you in full.",
     "authentic, genuine, fake, real, counterfeit, original, replica"),
    ("Authenticity", "How do you authenticate a watch?",
     "Our 4-step process: 01 Inspection of case, dial, serials and bracelet; 02 Movement check on a timegrapher for rate, amplitude and beat error; 03 Light polishing only when you ask for it; 04 Certification with photos and a signed report.",
     "authenticate, authentication, inspection, verify, check, process, timegrapher, certified"),
    ("Authenticity", "Do watches come with box and papers?",
     "Each listing states clearly whether the original box and papers are included — look for the 'Box & Papers' badge. Watches without them are priced accordingly and still come with our own certificate.",
     "box, papers, box and papers, warranty card, documents, full set"),
    ("Warranty", "What warranty do I get?",
     "Every watch includes a 12-month Maison Heure mechanical warranty covering the movement. It does not cover accidental damage, water damage from unscrewed crowns, straps or crystals.",
     "warranty, guarantee, repair, broken, covered"),
    ("Delivery", "How long does delivery take?",
     "Insured standard delivery takes 5–7 business days and insured express takes 2–3 business days within India. Orders are dispatched after a final authentication check, usually within 24 hours.",
     "delivery, shipping time, how long, arrive, dispatch, days, express"),
    ("Delivery", "Is shipping insured?",
     "Yes. Every parcel is fully insured for its value from our vault to your door and requires an OTP and signature on delivery. Packaging is discreet with no branding on the outside.",
     "insured, insurance, safe, lost, stolen, signature, otp"),
    ("Returns", "What is your return policy?",
     "You can return any watch within 14 days of delivery if it is unworn and in the same condition, with all tags, the certificate and packaging. We arrange insured pickup and refund within 5 business days of inspection.",
     "return, returns, refund, exchange, money back, 14 days, cancel"),
    ("Payments", "Which payment methods do you accept?",
     "We accept UPI, credit and debit cards, net banking and bank transfer (RTGS/NEFT) for high-value orders. This demo site uses a simulated payment only — no real card details are ever collected.",
     "payment, pay, upi, card, credit, debit, emi, bank transfer, rtgs, neft"),
    ("Orders", "How do I track my order?",
     "Signed in? Open Account → My orders. Otherwise use the Track Order page with your order reference (e.g. MH-2026-000123) and the email you used at checkout. You'll see every step from Placed to Delivered, with the courier AWB number.",
     "track, tracking, order status, where is my order, awb, courier"),
    ("Selling", "Can I sell or consign my watch?",
     "Yes. Use the Sell page to tell us the brand, model, year, condition and asking price. A specialist replies within two business days with an offer to buy outright or to consign it on your behalf.",
     "sell, selling, consign, consignment, trade in, part exchange, offer"),
    ("Selling", "How is the resale price decided?",
     "We look at recent sales of the same reference, condition, completeness (box and papers), service history and current demand. The landing-page estimator gives a rough range; the final offer follows a physical inspection.",
     "price, pricing, valuation, value, worth, resale price, estimate, how much"),
    ("Delivery", "Do you ship internationally?",
     "Currently we ship only within India. International collectors can still buy and arrange collection from our Mumbai showroom by appointment.",
     "international, abroad, overseas, outside india, worldwide, ship to"),
    ("Service", "Do you service watches?",
     "Our watchmakers can service any watch you bought from us at a preferential rate. A full service typically takes 3–4 weeks and includes a fresh 12-month warranty.",
     "service, servicing, overhaul, maintenance, clean"),
    ("Orders", "Can I reserve a watch?",
     "When you start checkout we hold the watches in your bag for 15 minutes so nobody else can buy them. For longer holds, contact us and a specialist can reserve a piece for up to 48 hours.",
     "reserve, reservation, hold, keep aside, reserved"),
    ("Payments", "Can I negotiate the price?",
     "Our prices are already set close to the market, but we're happy to discuss offers on watches listed for more than 60 days. Use the contact form and mention the reference number.",
     "negotiate, negotiation, discount, offer, lower price, best price, deal"),
]

ERROR_CODES = [
    (400, "Bad Request", "The form or link sent something we couldn't understand, such as a malformed field or a broken query.", "Check the highlighted form fields and try again. If you followed a link, start again from the home page.", False),
    (401, "Unauthorized", "You need to be signed in for this — for example checkout, your wishlist or your account.", "Sign in or create an account; you'll be taken straight back to where you were.", False),
    (403, "Forbidden", "You don't have permission: the page belongs to another account (e.g. someone else's order), or your security (CSRF) token expired.", "Make sure you're signed in to the right account. If you left a form open for a long time, refresh the page and submit it again.", False),
    (404, "Not Found", "The page or watch doesn't exist — the address may be mistyped or the listing was removed.", "Check the address, or browse the shop. Sold watches stay listed, so a missing one was taken down.", False),
    (405, "Method Not Allowed", "The page was requested in a way it doesn't accept, e.g. opening a form-only action like 'Add to Bag' directly.", "Use the buttons on the page rather than typing the address.", False),
    (429, "Too Many Requests", "You've made too many attempts in a short time — chat messages, order look-ups or sign-ins are rate limited to protect accounts.", "Wait about a minute (order look-ups: up to 10 minutes) and try again.", False),
    (470, "Watch Already Sold", "Maison Heure-specific: every watch is one of a kind, and the one in your bag was bought or reserved by another collector while you were browsing.", "Remove it from your bag and look at similar watches — or ask the assistant to notify you when a similar piece arrives.", True),
    (500, "Internal Server Error", "Something went wrong on our side. It's our fault, not yours, and it has been logged.", "Try again in a moment. If it keeps happening, ask the assistant — it will open a support ticket for our team.", False),
    (503, "Service Unavailable", "We're under maintenance or a service we depend on (database, payments) is temporarily down.", "Try again in a few minutes. The /health/ page shows which services are running.", False),
]


def seed(apps, schema_editor):
    FAQ = apps.get_model("support", "FAQ")
    ErrorCode = apps.get_model("support", "ErrorCode")
    for order, (category, question, answer, keywords) in enumerate(FAQS, start=1):
        FAQ.objects.get_or_create(
            question=question, defaults={"answer": answer, "category": category, "keywords": keywords, "order": order}
        )
    for code, title, explanation, fix, site_specific in ERROR_CODES:
        ErrorCode.objects.get_or_create(
            code=code, defaults={"title": title, "explanation": explanation, "fix": fix, "is_site_specific": site_specific}
        )


def unseed(apps, schema_editor):
    apps.get_model("support", "FAQ").objects.filter(question__in=[f[1] for f in FAQS]).delete()
    apps.get_model("support", "ErrorCode").objects.filter(code__in=[c[0] for c in ERROR_CODES]).delete()


class Migration(migrations.Migration):
    dependencies = [("support", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
