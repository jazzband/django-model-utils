import os

INSTALLED_APPS = (
    'model_utils',
    'tests',
)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("DB_NAME", "modelutils"),
        "USER": os.environ.get("DB_USER", 'postgres'),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", 5432)
    },
}
SECRET_KEY = 'dummy'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
