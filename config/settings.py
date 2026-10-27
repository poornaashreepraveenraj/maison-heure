"""
Django settings for Maison Heure.

Every secret and environment-specific value is read from environment
variables (see .env.example). Nothing sensitive is hard-coded here.
"""
import os
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Tiny .env loader so local development needs no extra package.

    Real environment variables always win over values in the file.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in (env(name) or default).split(",") if item.strip()]


# --- Core -----------------------------------------------------------------

ON_VERCEL = bool(env("VERCEL"))
# DEBUG is off by default on Vercel, on by default locally.
DEBUG = env_bool("DEBUG", default=not ON_VERCEL)

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver,.vercel.app")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
    "cart",
    "orders",
    "support",
    "accounts",
    "sell",
]

MIDDLEWARE = [
    "support.middleware.RequestLoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.bag",
                "support.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ---------------------------------------------------------------

def parse_database_url(url):
    """Turn a postgres:// URL (user, password, host, port, db name, ?sslmode=) into Django config.

    Parsed with urllib so no extra dependency (dj-database-url) is needed.
    """
    parsed = urlparse(url)
    if parsed.scheme in {"postgres", "postgresql", "pgsql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "OPTIONS": dict(parse_qsl(parsed.query)),
            # Serverless functions are short-lived; don't hold connections open.
            "CONN_MAX_AGE": 0,
        }
    if parsed.scheme == "sqlite":
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": parsed.path.lstrip("/") or BASE_DIR / "db.sqlite3"}
    raise ImproperlyConfigured(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")


DATABASE_URL = env("DATABASE_URL")
DATABASES = {
    "default": parse_database_url(DATABASE_URL)
    if DATABASE_URL
    else {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Auth -------------------------------------------------------------------

# scrypt is built into Django, memory-hard, and ~5x faster here than Django's
# default PBKDF2 (0.5 s vs 2.5 s per sign-in), which matters on serverless hosting.
# PBKDF2 stays in the list so older hashes still verify; they are upgraded on next login.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.ScryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "store:home"


# --- I18N / static ------------------------------------------------------------

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- Cache (rate limiting + FX rate caching) ----------------------------------
# LocMem is per-process. Good enough for a demo; Redis would be the upgrade.

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "maison-heure",
    }
}


# --- Email (console backend: confirmation emails print to the log) ----------

EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Maison Heure <orders@maisonheure.example>")


# --- Third-party services -----------------------------------------------------

ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-opus-5-5")
MONGODB_URI = env("MONGODB_URI", "")
MONGODB_DB = env("MONGODB_DB", "maison_heure")
FX_API_URL = env("FX_API_URL", "https://open.er-api.com/v6/latest/INR")

# Rate limits: name -> (max hits, window in seconds)
RATE_LIMITS = {
    "chat": (20, 60),
    "track": (5, 600),   # failed order lookups per IP
    "login": (8, 600),   # failed logins per IP
}


# --- Security ------------------------------------------------------------------

CSRF_FAILURE_VIEW = "support.views.csrf_failure"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Kept small on purpose; raise once HTTPS on the final domain is stable.
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "3600"))


# --- Logging (stdout, which Vercel captures) ----------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "maisonheure": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
