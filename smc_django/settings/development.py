"""
Development settings for smc_django project.
"""

from .base import *

# Development specific settings
DEBUG = True

# Additional apps for development
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# Database for development (SQLite)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Debug toolbar configuration
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Less strict security for development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Cache (disabled for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Logging for development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['inventory']['level'] = 'DEBUG'