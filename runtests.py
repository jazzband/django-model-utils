#!/usr/bin/env python

import os, sys

from django.conf import settings
import django


DEFAULT_SETTINGS = dict(
    INSTALLED_APPS=(
        'django.contrib.contenttypes',
        'model_utils',
        'model_utils.tests',
        ),
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3"
            }
        },
    )


def runtests(*test_args):
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    # Compatibility with Django 1.7's stricter initialization
    if hasattr(django, 'setup'):
        django.setup()

    if not test_args:
        test_args = ['tests']

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    from django.test.simple import DjangoTestSuiteRunner
    failures = DjangoTestSuiteRunner(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
