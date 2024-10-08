"""
Django settings for collector project.
"""
import environ
import os
from pathlib import Path
from .localsettings import DEBUG, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, DB_SERVER

# these settings are platform-specific and may not be present
try:
    from .localsettings import GDAL_LIBRARY_PATH, GEOS_LIBRARY_PATH
except:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# use django-environ for some local settings
# https://django-environ.readthedocs.io/en/latest/quickstart.html
# https://django-environ.readthedocs.io/en/latest/tips.html
# (using Docker secrets with _FILE appended to the variable name

# Take environment variables from .env file (use this as backup in case we're not running in docker compose/stack)
# Normally, the primary source should be variables fed in through the compose.yml file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

env = environ.FileAwareEnv(
    # set casting, default value
    DEBUG=(bool, False),
    APP_DB_PASSWORD=(str, 'secret'),
    ROOT_DB_PASSWORD=(str, 'secret'),
    EMAIL_HOST_PASSWORD=(str, 'secret'),
    SECRET_KEY=(str, 'secret'),
)

# SECURITY WARNING: keep the secret key used in production secret!
# this should be imported from an unversioned local file
# called localsettings.py
# echo "SECRET_KEY='$(./manage.py generate_secret_key)'" > localsettings.py
SECRET_KEY=env("SECRET_KEY")

# DEBUG and ALLOWED_HOSTS should also be defined in localsettings.py
## DEBUG=False
## ALLOWED_HOSTS=[]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'csp', # content security policy
    'django_registration',
    'geoip2',
    'leaflet',
    'debug_toolbar',
    'django_extensions',
    'rest_framework',
    'rest_framework_gis',
    'pio',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_email',  # <- if you want email capability.
    'otp_yubikey',
    'two_factor',
    'two_factor.plugins.phonenumber',  # <- if you want phone number capability.
    'two_factor.plugins.email',  # <- if you want email capability.
    'two_factor.plugins.webauthn',
    'two_factor.plugins.yubikey',  # <- for yubikey capability.
]

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'collector.urls'
LOGIN_URL = 'two_factor:login'
LOGIN_REDIRECT_URL = 'two_factor:profile'

TWO_FACTOR_WEBAUTHN_RP_NAME = 'mapsurvey'
TWO_FACTOR_REMEMBER_COOKIE_AGE = 86400*14

ACCOUNT_ACTIVATION_DAYS = 2

INTERNAL_IPS = ['127.0.0.1',]

# enable SMTP if password is present
try:
    EMAIL_HOST_PASSWORD=env("EMAIL_HOST_PASSWORD")
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
CSP_FONT_SRC = ("'self'", 
                "https://fonts.googleapis.com", 
                "https://fonts.gstatic.com", 
                "https://cdnjs.cloudflare.com",)
CSP_FRAME_ANCESTORS = ("https://portlandstate.yul1.qualtrics.com/", "https://portlandstate.qualtrics.com/",)
CSP_IMG_SRC = ("'self'",
               'https://cdn.jsdelivr.net',
               'https://basemap.nationalmap.gov',
               'https://server.arcgisonline.com',
               'http://*.tile.openstreetmap.org',) # admin uses http: when running the test server on localhost
CSP_INCLUDE_NONCE_IN = ['script-src',]
CSP_SCRIPT_SRC = ("'self'", "'unsafe-hashes'", "'unsafe-inline'",
                  'https://cdn.jsdelivr.net',
                  )
CSP_STYLE_SRC = ("'self'", 
                 "'unsafe-inline'", 
                 'https://cdn.jsdelivr.net',
                 'https://cdnjs.cloudflare.com',
                 'https://fonts.googleapis.com/css',
                 )
CSP_STYLE_SRC_ELEM = ("'self'",
                      'http://cdnjs.cloudflare.com',
                      "https://fonts.googleapis.com", 
                      'https://cdn.jsdelivr.net',
                  )
CSP_WORKER_SRC = ("'self'", "blob:", "data:")

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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'csp.context_processors.nonce',
            ],
            'libraries': {
                #'csp': 'csp.templatetags.csp',
            }
        },
    },
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
            'options': '-c search_path=geodjango,public'
        },

        # trim the \n from the end of password, if present
        'PASSWORD': env("APP_DB_PASSWORD").replace('\n', ''),
        'HOST': DB_SERVER,
        'PORT': 5432,
    },
}

"""
    'admin': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'mapbe',
        'USER': 'postgres',

        # trim the \n from the end of password, if present
        'PASSWORD': env("ROOT_DB_PASSWORD").replace('\n', ''),
        'HOST': DB_SERVER,
        'PORT': DB_PORT,
    },
"""


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
except:
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
            "level": "DEBUG",
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
