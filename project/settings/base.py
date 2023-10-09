import os
import sys

import environ

# helpers and such
PROJECT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../../")
sys.path.append(os.path.join(PROJECT_PATH, "apps/"))
gettext = lambda s: s  # noqa

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(
        list,
        [
            "localhost",
        ],
    ),
    DEFAULT_FROM_EMAIL=(str, "djangocms4test@bnzk.ch"),
    SITE_ID=(int, 1),
    SENTRY_DSN=(str, None),
)
environ.Env.read_env(os.path.join(PROJECT_PATH, ".env"))


DEBUG = env("DEBUG")
# THUMBNAIL_DEBUG = True
# COMPRESS_ENABLED = False
# more live behavious, if you pleas..
# from deploy import *

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

DATABASES = {
    "default": env.db_url(),
}


# some django things
ADMINS = [
    # no more! sentry FTW. ('BNZK', 'support@bnzk.ch'),
]
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_CONFIG = env.email_url(default="")  # intended fail if env var not present!
vars().update(EMAIL_CONFIG)


# enable when behind nginx proxy
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTOCOL', 'https')
# SECURE_PROXY_SSL_HEADER = env.tuple('SECURE_PROXY_SSL_HEADER', None)
INTERNAL_IPS = (
    "127.0.0.1",
    "0.0.0.0",
)
SITE_ID = env.int("SITE_ID")
ROOT_URLCONF = "project.urls"
# default time zone
TIME_ZONE = "Europe/Zurich"
# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True
USE_I18N = True
USE_L10N = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
WSGI_APPLICATION = "project.wsgi.application"
SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"
TEST_RUNNER = "django.test.runner.DiscoverRunner"
SECRET_KEY = env.str("SECRET_KEY")


# some third party things

# opposite of DEBUG!
# HTML_MINIFY = True
# add p when needed
# EXCLUDE_TAGS_FROM_MINIFYING = ['custom', 'pre', 'textarea', 'p', 'script', 'style', ]
KEEP_COMMENTS_ON_MINIFYING = True
TEXTBLOCKS_SHOWKEY = True
# SENTRY_DSN = 'https://xxxxxx@sentry.io/1416363'
SENTRY_DSN = env("SENTRY_DSN", None)
# VERSION = str(subprocess.check_output(["git", "describe", "--tags"]).strip())
VERSION = "dev"


# middleware and templates
MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "cms.middleware.page.CurrentPageMiddleware",
    "cms.middleware.user.CurrentUserMiddleware",
    "cms.middleware.toolbar.ToolbarMiddleware",
    "cms.middleware.language.LanguageCookieMiddleware",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # insert your TEMPLATE_DIRS here
        ],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "sekizai.context_processors.sekizai",
                "cms.context_processors.cms_settings",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
                # 'django.template.loaders.eggs.Loader',
            ],
        },
    },
]
