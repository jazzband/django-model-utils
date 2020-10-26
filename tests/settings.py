import os

INSTALLED_APPS = (
    "model_utils",
    "tests",
)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("DJANGO_DATABASE_NAME_POSTGRES", "modelutils"),
        "USER": os.environ.get("DJANGO_DATABASE_USER_POSTGRES", "postgres"),
        "PASSWORD": os.environ.get("DJANGO_DATABASE_PASSWORD_POSTGRES", ""),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST_POSTGRES", ""),
    },
}
SECRET_KEY = "dummy"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
