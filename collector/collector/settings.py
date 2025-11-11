"""
Django settings for collector project.
"""
import environ
import os
from pathlib import Path
from .localsettings import * # for platform flexibility

from csp.constants import SELF, NONCE, UNSAFE_HASHES, UNSAFE_INLINE

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# use django-environ for some local settings
# https://django-environ.readthedocs.io/en/latest/quickstart.html
# https://django-environ.readthedocs.io/en/latest/tips.html
# (using Docker secrets with _FILE appended to the variable name

env = environ.FileAwareEnv(
    # set casting, default value
    DEBUG=(bool, False),
    DB_SERVER=(str, 'localhost'),
    DB_PORT=(int, 5432),
    DB_PASSWORD=(str, 'secret'),
    ROOT_DB_PASSWORD=(str, 'secret'),
    EMAIL_HOST_PASSWORD=(str, 'none'), # use this as a sentinel to trigger lookup in localsettings
    SECRET_KEY=(str, 'secret'),
)

# Take environment variables from .env file
# use this as backup in case we're not running in docker compose/stack
# Normally, the primary source should be variables fed in through the compose.yml file
# see .env.dist for an example
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# this should be imported from an unversioned local file
# called localsettings.py
# echo "SECRET_KEY='$(./manage.py generate_secret_key)'" > localsettings.py
SECRET_KEY=env("SECRET_KEY")

# DEBUG and ALLOWED_HOSTS should be defined in localsettings.py
# DEBUG=False
# ALLOWED_HOSTS=['pointitout.app',
#               '.localhost',
#               '127.0.0.1',
#               '[::1]',
#               '172.232.170.62',]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth email URLs
    'django.contrib.flatpages',  # For static content pages
    'django.contrib.gis',
    'djgeojson',
    'django_json_widget',
    'csp', # content security policy, settings under CONTENT_SECURITY_POLICY

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.mfa',
    'django.contrib.humanize',

    'geoip2',
    'leaflet',
    'django_extensions',
    'rest_framework',
    'rest_framework_gis',
    'pio',
]

# Sites framework configuration for allauth
SITE_ID = 1

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'collector.urls'
LOGIN_URL = 'allauth:login'
LOGIN_REDIRECT_URL = 'admin:index'

TWO_FACTOR_WEBAUTHN_RP_NAME = 'mapsurvey'
TWO_FACTOR_REMEMBER_COOKIE_AGE = 86400*14

# ALLAUTH settings
ACCOUNT_CHANGE_EMAIL=True
ACCOUNT_CONFIRM_EMAIL_ON_GET=True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/admin/'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = '/admin/'
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = "address"

MFA_SUPPORTED_TYPES = ["totp", "webauthn", "recovery_codes"]
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_TRUST_ENABLED = True

ACCOUNT_ACTIVATION_DAYS = 2

# 24.21.163.40 is dev IP - remove when done
# 172.19.0.1 is docker network gateway IP - setting this here should enable debug everywhere.
INTERNAL_IPS = ['127.0.0.1','24.21.163.40','172.19.0.1',]

def callback(request):
    return True

# enable SMTP if password is present
try:
    EMAIL_HOST_PASSWORD=env("EMAIL_HOST_PASSWORD")

    if (EMAIL_HOST_PASSWORD=='none'):
        from .localsettings import EMAIL_HOST_PASSWORD

    # use SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST='smtp.gmail.com'
    EMAIL_PORT=587
    EMAIL_HOST_USER='chris.ghormley'
    EMAIL_USE_TLS=True
    EMAIL_TIMEOUT=120
except ImportError:
    # don't really send email - log to console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



# Content Security Policy
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        'connect-src':      [SELF,
                             'https://cdn.jsdelivr.net'],
        'font-src':        [SELF,
                            "https://fonts.googleapis.com",
                            "https://fonts.gstatic.com",
                            "https://cdnjs.cloudflare.com"],
        'frame-ancestors': ["https://portlandstate.yul1.qualtrics.com/",
                            "https://portlandstate.qualtrics.com/"],
        'img-src':         [SELF,
                            'data:', # allow inline svg, e.g., for QR codes
                            'https://cdn.jsdelivr.net',
                            'https://basemap.nationalmap.gov',
                            'https://server.arcgisonline.com',
                            # admin uses http: when running
                            # the test server on localhost
                          'http://*.tile.openstreetmap.org'],
        'script-src':      [SELF,
                            NONCE,
                            UNSAFE_HASHES,
                            UNSAFE_INLINE,
                            'https://cdn.jsdelivr.net'],
        'style-src':       [SELF,
                            UNSAFE_INLINE,
                            'https://cdn.jsdelivr.net',
                            'https://cdnjs.cloudflare.com',
                            'https://fonts.googleapis.com/css'],
        'style-src-elem':  [SELF,
                            'http://cdnjs.cloudflare.com',
                            "https://fonts.googleapis.com",
                            'https://cdn.jsdelivr.net'],
        'worker-src':      [SELF, "blob:", "data:"]
    }
}

# https://developers.yubico.com/PKI/yubico-fido-ca-1.pem
yubico_u2f_ca = """-----BEGIN CERTIFICATE-----
MIIDHjCCAgagAwIBAgIEG0BT9zANBgkqhkiG9w0BAQsFADAuMSwwKgYDVQQDEyNZ
dWJpY28gVTJGIFJvb3QgQ0EgU2VyaWFsIDQ1NzIwMDYzMTAgFw0xNDA4MDEwMDAw
MDBaGA8yMDUwMDkwNDAwMDAwMFowLjEsMCoGA1UEAxMjWXViaWNvIFUyRiBSb290
IENBIFNlcmlhbCA0NTcyMDA2MzEwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQC/jwYuhBVlqaiYWEMsrWFisgJ+PtM91eSrpI4TK7U53mwCIawSDHy8vUmk
5N2KAj9abvT9NP5SMS1hQi3usxoYGonXQgfO6ZXyUA9a+KAkqdFnBnlyugSeCOep
8EdZFfsaRFtMjkwz5Gcz2Py4vIYvCdMHPtwaz0bVuzneueIEz6TnQjE63Rdt2zbw
nebwTG5ZybeWSwbzy+BJ34ZHcUhPAY89yJQXuE0IzMZFcEBbPNRbWECRKgjq//qT
9nmDOFVlSRCt2wiqPSzluwn+v+suQEBsUjTGMEd25tKXXTkNW21wIWbxeSyUoTXw
LvGS6xlwQSgNpk2qXYwf8iXg7VWZAgMBAAGjQjBAMB0GA1UdDgQWBBQgIvz0bNGJ
hjgpToksyKpP9xv9oDAPBgNVHRMECDAGAQH/AgEAMA4GA1UdDwEB/wQEAwIBBjAN
BgkqhkiG9w0BAQsFAAOCAQEAjvjuOMDSa+JXFCLyBKsycXtBVZsJ4Ue3LbaEsPY4
MYN/hIQ5ZM5p7EjfcnMG4CtYkNsfNHc0AhBLdq45rnT87q/6O3vUEtNMafbhU6kt
hX7Y+9XFN9NpmYxr+ekVY5xOxi8h9JDIgoMP4VB1uS0aunL1IGqrNooL9mmFnL2k
LVVee6/VR6C5+KSTCMCWppMuJIZII2v9o4dkoZ8Y7QRjQlLfYzd3qGtKbw7xaF1U
sG/5xUb/Btwb2X2g4InpiB/yt/3CpQXpiWX/K4mBvUKiGn05ZsqeY1gx4g0xLBqc
U9psmyPzK+Vsgw2jeRQ5JlKDyqE0hebfC1tvFu0CCrJFcw==
-----END CERTIFICATE-----"""

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / "templates" ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
#                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'csp.context_processors.nonce',

                # `allauth` needs this from django
                'django.template.context_processors.request',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]

WSGI_APPLICATION = 'collector.wsgi.application'


# weird permissions issue when trying to start new database
# trying to follow advice below:
# https://stackoverflow.com/questions/38944551/steps-to-troubleshoot-django-db-utils-programmingerror-permission-denied-for-r
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mapbe',
        'USER': 'geodjango',
        'OPTIONS': {
            'options': '-c search_path=geodjango,public',
            'sslmode': 'require',
        },

        'HOST': env("DB_SERVER"),
        'PORT': env("DB_PORT"),

        # trim the \n from the end of password, if present
        'PASSWORD': env("DB_PASSWORD").replace('\n', ''),
    },
}

SERIALIZATION_MODULES = {
    'geojson' : 'djgeojson.serializers'
}

# declare this explicitly so we can enable ManifestStaticFiles
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
#        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# non-app staticfiles
STATICFILES_DIRS = [
    BASE_DIR / "collector/static",
]

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

try:
    from .localsettings import TIME_ZONE, USE_TZ
except ImportError:
    TIME_ZONE = 'UTC'
    USE_TZ = False


USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "app_staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# leaflet settings for a side test, not production
LEAFLET_CONFIG = {
    'DEFAULT_ZOOM': 12,
    'MAX_ZOOM': 12,
    'MIN_ZOOM':12,
    'SCALE': 'both',
    'ATTRIBUTION_PREFIX': '',
    'TILES': [('','//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png','')],
}

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],

    # consider using django-knox for authenticated API calls
    #'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),

    # Rate limiting - NO DEFAULT_THROTTLE_CLASSES (explicit per endpoint)
    # Throttle classes are applied individually to each viewset
    'DEFAULT_THROTTLE_RATES': {
        'survey_points_anon': '20/min',      # Anonymous survey submissions
        'survey_points_auth': '100/min',     # Authenticated survey submissions
        'map_layers': '500/hour',             # Map layer data (read-only)
        'mapconfigs': '200/hour',             # Map configurations (read-only)
        'feature_layers': '500/hour',         # GeoJSON feature layers (read-only)
        'visitor_behavior': '100/hour',       # Visitor behavior logging
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose"
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.template": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
        }
    }
}

# MaxMind geoip2 databases
# Country Database URL
# https://download.maxmind.com/geoip/databases/GeoLite2-Country/download?suffix=tar.gz
# SHA256 URL
# https://download.maxmind.com/geoip/databases/GeoLite2-Country/download?suffix=tar.gz.sha256
# City Database URL
# https://download.maxmind.com/geoip/databases/GeoLite2-City-CSV/download?suffix=zip
# SHA256 URL
# https://download.maxmind.com/geoip/databases/GeoLite2-City-CSV/download?suffix=zip.sha256
GEOIP_PATH = BASE_DIR / "geoip"
