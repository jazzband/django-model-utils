#!/usr/bin/env python
import os
import sys

from django.conf import settings
import django

DEFAULT_SETTINGS = dict(
    INSTALLED_APPS=(
        'model_utils',
        'tests',
    ),
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3"
        }
    },
    SILENCED_SYSTEM_CHECKS=["1_7.W001"],
)


def run(command):
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    # Compatibility with Django 1.7's stricter initialization
    if hasattr(django, 'setup'):
        django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    appdir = os.path.join(parent, 'model_utils')
    os.chdir(appdir)

    from django.core.management import call_command

    call_command('%smessages' % command)


if __name__ == '__main__':
    if (len(sys.argv)) < 2 or (sys.argv[1] not in {'make', 'compile'}):
        print("Run `translations.py make` or `translations.py compile`.")
        sys.exit(1)
    run(sys.argv[1])
