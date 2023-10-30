from .base import gettext

CMS_TOOLBAR_URL__ENABLE = 'edit'
# just in case...
DJANGOCMS_MISC_UNTRANSLATED_PLACEHOLDERS = False
CMS_CONFIRM_VERSION4 = True

CMS_TEMPLATES = (
    ("djangocms4test/standard.html", gettext("Standard")),
    ("djangocms4test/home.html", gettext("Homepage")),
)

CMS_CACHE_DURATIONS = {
    "content": 180,
    "menus": 180,
    "permissions": 180,
}

# CMS_CACHE_PREFIX = "cms-" default

CMS_PAGE_CACHE = True
CMS_PLACEHOLDER_CACHE = True
CMS_PLUGIN_CACHE = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "de"
LANGUAGES = (
    ("de", gettext("Deutsch")),
    ("en", gettext("English")),
    ("it", gettext("Italiano")),
)

CMS_LANGUAGES = {
    1: [
        {
            "code": "de",
            "name": ("DE"),
            "fallbacks": ["en", "fr"],
            "public": True,
        },
        {
            "code": "en",
            "name": ("EN"),
            "fallbacks": ["fr", "de"],
            "public": True,
        },
        {
            "code": "it",
            "name": ("IT"),
            "fallbacks": ["en", "de"],
            "public": True,
        },
    ],
}

# CMS_PLUGIN_PROCESSORS = (
#    'djangocms4test.plugin_processors.default_div',
# )
