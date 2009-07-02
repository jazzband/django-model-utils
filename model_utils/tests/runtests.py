#!/usr/bin/env python

import os, sys

parent = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))

sys.path.insert(0, parent)

from django.core.management import setup_environ, call_command
from model_utils.tests import test_settings
setup_environ(test_settings, 'model_utils.tests.test_settings')
call_command('test', 'tests')
