#!/usr/bin/env python

import os, sys

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


def runtests():
    if not settings.configured:
        settings.configure(**DEFAULT_SETTINGS)

    django.setup()

    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    from django.test.runner import DiscoverRunner
    runner_class = DiscoverRunner
    test_args = ['tests']

    failures = runner_class(
        verbosity=1, interactive=True, failfast=False).run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests()
