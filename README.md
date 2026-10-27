<p><img src="static/img/logo.svg" alt="Maison Heure — pre-owned fine watches" width="380"></p>

# Maison Heure

The logo is an **MH monogram**: the centre strokes of the M are a watch's hands set at 10:10 (thick hour hand, thin minute hand), inside a dial ring with a champagne-gold pivot and lume pip at 12. The site uses a **Noir & Champagne** palette (ivory pages, noir hero and footer, champagne-gold accents, bordeaux badges; tokens in `static/css/tokens.css`). Live UI: the hero watch shows the visitor's real time, shop filters and search update instantly, checkout shows a live hold countdown, product pages warn if a watch sells while open, order timelines and `/health/` refresh themselves. Files: `static/img/logo.svg` (lockup), `static/img/logo-mark.svg` (monogram), `static/img/favicon.svg`, and `templates/partials/logo.html` (inline version that takes the text colour).

**Task title:** *Maison Heure — A Luxury Pre-Owned Watch Resale Platform with an AI Support Assistant*

Maison Heure is a responsive Django website for buying and selling authenticated pre-owned luxury watches in India. It includes a shop with filters, a product gallery, a bag with 15-minute reservations, a 3-step checkout (demo payment), order tracking, consignments, and a concierge chat on every page. The concierge answers from the FAQ and error-code database, looks up orders, falls back to Claude, and opens a support ticket when it can't answer.

| | |
|---|---|
| **Live site** | https://YOUR-PROJECT.vercel.app *(add after deploying)* |
| **GitHub** | https://github.com/YOUR-USERNAME/maison-heure *(add after pushing)* |
| **Admin** | `/admin/` (create a superuser) |
| **Health** | `/health/` and `/health/?format=json` |

> Maison Heure is an original student brand. It is not affiliated with any watch manufacturer; brand and model names describe the (sample) pre-owned stock. 17 watches use free photos from Unsplash (see [Photo credits](#photo-credits)); the rest use generated illustrations with no logos.

---

## Screenshots

Add screenshots here before submitting (landing page, shop, product, chat answering a question, 404 page, mobile view, `/admin/` ticket list, MongoDB collections).

---

## Requirement → feature map

| Marking column | Where it is implemented |
|---|---|
| **Website (/10)** | 20+ responsive pages (see URL list below), with Men's / Women's / Unisex edits (`?gender=men\|women\|unisex`; unisex pieces appear in both). Chat widget in `templates/partials/chat.html`, included by `templates/base.html` on every page. |
| **FAQ (/10)** | `support.FAQ` model, 15 FAQs seeded by `support/migrations/0002_seed_faq_errorcodes.py`, shown at `/faq/`. |
| **Error codes (/15)** | `support.ErrorCode` with 400, 401, 403, 404, 405, 429, 500, 503 plus the site-specific **470 Watch Already Sold**. Shown at `/error-codes/`. Custom `404.html`, `500.html`, `403.html`, `400.html`, `errors/429.html` and `errors/470.html`, each with an **Ask the assistant** button. 470 is raised for real in `cart/views.py` and `orders/services.py`. |
| **AI assistant (/25)** | `support/assistant.py`: error codes → orders → catalogue → FAQ scoring → Claude (`claude-opus-5-5`, low effort, 15 s timeout, server-side refusal fallback) → **SupportTicket**. API: `POST /api/chat/`. |
| **Backend & data (/15)** | SQL: watches, orders, tickets, FAQs, consignments and more (Django ORM; SQLite locally, PostgreSQL in production). MongoDB: `chat_logs` and `feedback` collections (`support/mongo.py`). Every model is registered in admin with filters, search, inlines and actions. |
| **Deployment & security (/15)** | Vercel (`vercel.json`, `build_files.sh`, `app = application` in `config/wsgi.py`). Every secret comes from an env var, and `.env` is git-ignored. CSRF on all forms and `fetch` calls, secure cookies, HSTS, SSL redirect and `X_FRAME_OPTIONS=DENY` when `DEBUG=False`. `DEBUG` defaults to False on Vercel. |
| **Monitoring & feedback (/5)** | `support/middleware.py` logs method, path, status, duration, user and IP for every request. `/health/` page plus JSON. 👍/👎 feedback under every assistant answer is stored in MongoDB. |
| **Viva (/5)** | One app per responsibility, business logic in `services.py` / `assistant.py` / `pricing.py`, comments where logic isn't obvious, 70 automated tests (`python manage.py test`). |
| **Third-party API with timeout + fallback** | `support/rates.py`: open.er-api.com with `timeout=3`, a 10-minute cache and static fallback rates. `GET /api/rates/` returns `source: live\|fallback`, and the UI shows "Live rates" or "Showing fallback rates". |

---

## Tech stack

Django 6 · Django templates · vanilla HTML/CSS/JS · SQLite / PostgreSQL (`psycopg`) · MongoDB Atlas (`pymongo`) · Anthropic Python SDK (`anthropic`) · Vercel.

```
config/     settings (all env-driven), urls, wsgi (Vercel entry)
store/      Brand, Watch, WatchImage, Wishlist; home, shop, product, /api/watches/
cart/       session bag, pricing (GST margin scheme, promo, shipping), error 470
orders/     Address, Order, OrderItem, OrderStatusEvent; checkout, tracking
support/    FAQ, ErrorCode, SupportTicket, ContactMessage; assistant, mongo, rates,
            rate limiting, request-logging middleware, health, error handlers
accounts/   register, login (rate limited), logout (POST), dashboard, wishlist
sell/       Consignment form
templates/  base + partials (nav, footer, chat, product_card, badge, section_head …)
static/     css/tokens.css, base.css, components.css, pages.css; js/main.js, chat.js,
            shop.js, checkout.js; img/watches/*.svg (generated placeholders)
scripts/    generate_watch_images.py (re-creates the placeholder SVGs)
```

---

## Run locally

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env  (then edit values)
python manage.py migrate         # creates tables AND seeds watches, FAQs, error codes
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. To see the custom 404/500 pages locally, set `DEBUG=False` in `.env` and run `python manage.py runserver --insecure` (the `--insecure` flag keeps static files working).

### Tests

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

### Local URLs

| Page | URL |
|---|---|
| Landing | `/` |
| Shop (filters, search, sort, load more) | `/shop/` |
| Men's / Women's / Unisex | `/shop/?gender=men`, `/shop/?gender=women`, `/shop/?gender=unisex` |
| Product detail | `/watch/rolex-submariner-date-126610ln/` |
| Bag | `/bag/` |
| Checkout (shipping → delivery → payment) | `/checkout/`, `/checkout/delivery/`, `/checkout/payment/` |
| Order confirmation | `/orders/MH-2026-000001/confirmed/` |
| Order page / tracking | `/orders/MH-2026-000001/`, `/track/` |
| My orders | `/account/orders/` |
| Account dashboard | `/account/` |
| Wishlist | `/account/wishlist/` |
| Sell your watch | `/sell/` |
| About / authentication | `/about/` |
| FAQ | `/faq/` |
| Error codes | `/error-codes/` |
| Contact | `/contact/` |
| Register / login / logout (POST) | `/register/`, `/login/`, `/logout/` |
| Health | `/health/`, `/health/?format=json` |
| JSON APIs | `/api/watches/?brand=rolex`, `/api/rates/`, `POST /api/chat/`, `POST /api/feedback/` |
| Custom 404 | any unknown URL, e.g. `/does-not-exist/` |
| Custom 500 (staff only) | `/debug/500/` |
| Admin | `/admin/` |

Demo promo code: **WELCOME10** (10% off).

---

## Environment variables

| Variable | Required | Example / default | Purpose |
|---|---|---|---|
| `SECRET_KEY` | **Yes in production** | long random string | Django signing key. The app refuses to start without it when `DEBUG=False`. |
| `DEBUG` | No | `False` on Vercel, `True` locally | Never `True` in production. |
| `ALLOWED_HOSTS` | Yes | `your-project.vercel.app,.vercel.app` | Hostnames allowed to serve the site. |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://your-project.vercel.app` | Needed for HTTPS form posts. |
| `DATABASE_URL` | **Yes in production** | `postgres://user:pass@host:5432/db?sslmode=require` | PostgreSQL (Neon / Vercel Postgres). Empty = SQLite. |
| `MONGODB_URI` | Recommended | `mongodb+srv://…` | Chat logs + feedback. Empty = logging off; the site still works. |
| `MONGODB_DB` | No | `maison_heure` | Mongo database name. |
| `ANTHROPIC_API_KEY` | Optional | `sk-ant-…` | Enables the Claude fallback step of the assistant. |
| `ANTHROPIC_MODEL` | No | `claude-opus-5-5` | Model for the fallback. |
| `FX_API_URL` | No | `https://open.er-api.com/v6/latest/INR` | Currency API. |
| `SECURE_HSTS_SECONDS` | No | `3600` | HSTS max-age in production. |

---

## Deploy to Vercel (step by step)

1. **Database.** Create a free PostgreSQL database (Neon or Vercel Postgres) and copy its connection string.
2. **MongoDB.** Create a free MongoDB Atlas cluster, add a database user, and under *Network Access* allow `0.0.0.0/0`. Copy the `mongodb+srv://` URI.
3. **GitHub.** Push this folder to a new repository (`.env` and `db.sqlite3` are git-ignored).
4. **Vercel.** *Add New → Project → Import* the repository. Leave the framework preset as *Other*; `vercel.json` controls the build.
5. **Environment variables.** Add every variable from the table above (Production and Preview). Set `DEBUG=False`.
6. **Deploy.** `build_files.sh` installs requirements, runs `collectstatic` and `migrate`, so the Postgres database is created and seeded.
7. **Admin user.** On your machine, set `DATABASE_URL` to the production database and run `python manage.py createsuperuser`.
8. Open the live HTTPS URL and work through the checklist below. Put the live link and GitHub link at the top of this README.

---

## Launch checklist (12 items)

| # | Check | How to verify |
|---|---|---|
| 1 | Live HTTPS link opens the landing page | Open the Vercel URL |
| 2 | Works on a real phone | Nav drawer, shop filters drawer, product sticky "Add to Bag", checkout, chat bottom sheet |
| 3 | Wrong address shows the custom 404 with "Ask the assistant" | `/this-does-not-exist/` |
| 4 | 500 page is custom | Sign in as staff, open `/debug/500/` |
| 5 | Chat widget on every page and answers an FAQ | Ask "Is it authentic?" |
| 6 | Chat explains an error code | Ask "What does error 470 mean?" or "error 429" |
| 7 | Unanswerable question creates a ticket visible in admin | Ask something unrelated, then check `/admin/support/supportticket/` |
| 8 | FAQ page shows ≥ 10 FAQs from the database | `/faq/` (15 seeded) |
| 9 | Chat logs + feedback in MongoDB | Atlas → `maison_heure.chat_logs` and `maison_heure.feedback` after chatting and clicking 👍/👎 |
| 10 | `/health/` shows database, MongoDB and FX API status | `/health/` and `/health/?format=json` |
| 11 | No secrets in the repo | `git grep -nE "sk-ant-\|mongodb\+srv://[^.]*:[^@]*@\|postgres://[^:]*:[^@]*@" -- ":!.env.example" ":!README.md"` returns nothing (those two files only hold `user:password` placeholders), and `git check-ignore .env` prints `.env` |
| 12 | README has live link, GitHub link, setup, env table and a proposed improvement | This file |

---

## Known limitations

- **Demo payments only.** No card data is ever collected. The payment step simulates success or a decline.
- **Sample data.** Watches, prices, reviews, press names and the market ticker are illustrative.
- **Images.** 17 watches use free Unsplash photos (served from Unsplash's CDN, so they need an internet connection); photos are representative of the model, not of the individual sample listing. The remaining watches use generated SVG illustrations in `static/`. The Unsplash License covers the photos but not the brand trademarks visible on the dials, which are shown here only to identify the (sample) items for sale. To use more real photos, open `/admin/` → Watches → a watch → Images and paste an HTTPS **Photo URL** (photos you own or that are licensed for reuse, ideally on a plain white/grey background). Give the main photo order 0 and a second angle order 1 (shown on card hover). Files uploaded through admin work locally, but Vercel's filesystem is read-only, so in production host photos externally (e.g. Cloudinary) and use the URL field. Consignment photos are collected as links for the same reason.
- **Rate limits and the FX cache live in memory** (per serverless instance). Redis would make them global.
- **Emails** use Django's console backend (they print to the logs).

## Photo credits

Product photos are free to use under the [Unsplash License](https://unsplash.com/license). Thank you to the photographers. Each product page also credits its photo and links back to it. The photos are added by `store/migrations/0007_unsplash_photos.py`.

| Watch | Photographer(s) | Unsplash photo(s) |
|---|---|---|
| Rolex Submariner Date | Patrick Langwallner | [1](https://unsplash.com/photos/a-black-watch-on-a-white-surface-GaHmbqNh5q8), [2](https://unsplash.com/photos/a-watch-on-a-blue-surface-Sik80UHsb1Y) |
| Rolex Datejust 41 | Damian Kamp | [1](https://unsplash.com/photos/man-wearing-a-luxury-wristwatch-on-his-arm-miLQOt3_sMQ) |
| Rolex Cosmograph Daytona | Cash Macanaya | [1](https://unsplash.com/photos/a-watch-with-a-cloudy-sky-5enLV7bg6iw) |
| Rolex Explorer | Carlos Esteves, Soban Ahmed | [1](https://unsplash.com/photos/silver-and-black-round-analog-watch-Ae3OHpJfngc), [2](https://unsplash.com/photos/wrist-wearing-a-silver-watch-on-a-light-blue-shirt-wEtMI-MSDCU) |
| Rolex Oyster Perpetual 36 | Ali Ccu | [1](https://unsplash.com/photos/rolex-watch-with-blue-dial-in-green-box-dQT79SjiO1g) |
| Rolex Lady-Datejust 28 | Yash Parashar | [1](https://unsplash.com/photos/silver-and-white-round-analog-watch-LWPPpkn6NEQ), [2](https://unsplash.com/photos/silver-link-bracelet-round-analog-watch-VfozQD-IgdA) |
| Rolex Datejust 36 | Laurenz Heymann, Phước Sang | [1](https://unsplash.com/photos/silver-and-gold-round-analog-watch-at-10-10-al6s6JpnZis), [2](https://unsplash.com/photos/a-close-up-of-a-two-tone-rolex-watch-with-diamonds-8PzBx71aecg) |
| Omega Speedmaster Moonwatch | Hans Gaber | [1](https://unsplash.com/photos/black-and-silver-round-analog-watch-x-BEn77CZ8Q), [2](https://unsplash.com/photos/silver-and-black-round-analog-watch-idSBXY2QWOE) |
| Omega Seamaster Diver 300M | John Torcasio | [1](https://unsplash.com/photos/a-close-up-of-a-luxury-stainless-steel-watch-_teOJRLWe0o) |
| Omega Constellation Pie-Pan | Francesco Dondi | [1](https://unsplash.com/photos/a-watch-sitting-on-top-of-a-brown-case-X-cRJrqFzHA) |
| Cartier Tank Louis Cartier | Studio Crevettes | [1](https://unsplash.com/photos/gold-and-black-analog-watch-in-box-Ju-6TPKXdBs) |
| Cartier Santos | Keyur Jadav | [1](https://unsplash.com/photos/a-close-up-of-a-wrist-watch-on-a-table-OneGplJm4ko) |
| Patek Philippe Nautilus | Diniy Salleh | [1](https://unsplash.com/photos/silver-and-blue-analog-watch-gaBYtKLzf-I), [2](https://unsplash.com/photos/silver-and-black-digital-watch-cDQi-wnmE88) |
| Audemars Piguet Royal Oak | Ahsan Khan | [1](https://unsplash.com/photos/a-close-up-of-a-watch-on-a-table-XDTnKDj9yCg) |
| Audemars Piguet Royal Oak Lady | m G | [1](https://unsplash.com/photos/a-wooden-watch-sitting-on-top-of-a-black-surface-FeiPAKIvSvg) |
| Tudor Black Bay Fifty-Eight | Fidel Fernando, Horology Hands | [1](https://unsplash.com/photos/a-watch-sitting-on-a-black-surface-with-gold-numbers-3K0LfPFBz9U), [2](https://unsplash.com/photos/a-watch-on-a-rock-ecOiTQFt9ho) |
| Tudor Pelagos | Joshua katt | [1](https://unsplash.com/photos/a-watch-sitting-on-top-of-a-black-table-Y7ztFMKsfV8), [2](https://unsplash.com/photos/a-blue-and-white-watch-sitting-on-top-of-a-bed-dOQelfcqwWA) |

## Proposed improvement

**Visual authentication assist.** Let sellers upload photos of the dial, caseback and movement on the Sell page. A vision-capable Claude model would compare them against the reference's known features (font, lume plots, rehaut engraving, calibre layout) and flag inconsistencies, with a confidence note, *before* a human authenticator inspects the watch. It would speed up valuations and catch obvious fakes early, and the final decision would stay with a person. A second, smaller step: semantic FAQ search with embeddings, so questions worded very differently from the FAQ still find the right answer before falling back to Claude.
