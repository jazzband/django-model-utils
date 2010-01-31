import os

BASE_DIR = os.path.dirname(__file__)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'model_utils',
    'model_utils.tests',
    )

DATABASE_ENGINE = 'sqlite3'

try:
    import south
    INSTALLED_APPS += ('south',)
except ImportError:
    pass

