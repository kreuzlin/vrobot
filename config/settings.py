"""Django settings for vrobot.ch.

All environment-specific values come from environment variables (see
`.env.example`). There is a single settings module; development and
production differ only in their environment.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)

# Read a local .env file if present. In Docker the variables are injected by
# Compose instead, so a missing file is fine.
environ.Env.read_env(BASE_DIR / ".env")

# --- Core -----------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    # First, so its templates (e.g. admin/index.html) override Django's.
    "core",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "events",
    "posts",
    "documents",
    "pages",
    "contact",
]

MIDDLEWARE = [
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database -------------------------------------------------------------

# PostgreSQL only (ADR 0003), e.g. postgres://user:password@db:5432/vrobot
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Authentication -------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation -------------------------------------------------

# The website is German only (Swiss German spelling).
LANGUAGE_CODE = "de-ch"
TIME_ZONE = "Europe/Zurich"
USE_I18N = True
USE_TZ = True

# --- Static and media files -----------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = env.path("STATIC_ROOT", default=BASE_DIR / "staticfiles")

MEDIA_URL = "media/"
MEDIA_ROOT = env.path("MEDIA_ROOT", default=BASE_DIR / "media")

# --- Site ---------------------------------------------------------------

SITE_NAME = "Verein Robotik Talente"
SITE_SHORT_NAME = "VRoboT"
# Document title of the home page; other pages use "<page> – VRoboT".
SITE_TITLE = f"{SITE_SHORT_NAME} – {SITE_NAME}"
# Default meta description for pages that do not set their own.
SITE_DESCRIPTION = (
    "Der Verein Robotik Talente (VRoboT) fördert Kinder und Jugendliche, "
    "die sich für Robotik und Programmieren begeistern."
)
GEARSBOT_URL = env("GEARSBOT_URL", default="https://gears.aposteriori.com.sg/")

# --- Email ----------------------------------------------------------------

# Development prints emails to the console; production uses Hostpoint SMTP
# (ADR 0010).
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=465)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Recipients of contact form messages (comma-separated in the environment).
CONTACT_RECIPIENTS = env.list("CONTACT_RECIPIENTS", default=[])
# Contact messages older than this are deleted by
# `manage.py delete_old_contact_messages` (data protection).
CONTACT_MESSAGE_RETENTION_DAYS = env.int("CONTACT_MESSAGE_RETENTION_DAYS", default=365)

# --- Logging ------------------------------------------------------------

# Log to stdout/stderr; Docker collects the output.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        # 404/403 are expected noise; access logs come from Caddy.
        "django.request": {"level": "ERROR"},
    },
}

# --- Security (production) ------------------------------------------------

# Caddy terminates TLS and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
