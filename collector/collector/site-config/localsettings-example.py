SECRET_KEY=r"<generate with ./manage.py generate_secret_key>"
DEBUG=True
ALLOWED_HOSTS=['.localhost', '127.0.0.1', '[::1]']

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'https://example.com',
]

DB_SERVER = 'postgis'
DB_PASSWD = 'secret'
DB_PORT = '5432'

ADMINS = [('Chris', 'cgh2@pdx.edu',),]
EMAIL_HOST_PASSWORD = 'secret'

TIME_ZONE = 'America/Los_Angeles'
USE_TZ = False

# use the cookie-based session engine
SESSION_ENGINE='django.contrib.sessions.backends.signed_cookies'
