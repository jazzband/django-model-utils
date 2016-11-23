from __future__ import unicode_literals

import django
from django.db.models.fields import FieldDoesNotExist
from django.core.management import call_command
from django.test import TestCase

from model_utils.fields import get_excerpt
from model_utils.tests.models import (
    Article,
    StatusFieldDefaultFilled,
)
from model_utils.tests.helpers import skipUnless


class MigrationsTests(TestCase):
    @skipUnless(django.VERSION >= (1, 7, 0), "test only applies to Django 1.7+")
    def test_makemigrations(self):
        call_command('makemigrations', dry_run=True)


class GetExcerptTests(TestCase):
    def test_split(self):
        e = get_excerpt("some content\n\n<!-- split -->\n\nsome more")
        self.assertEqual(e, 'some content\n')

    def test_auto_split(self):
        e = get_excerpt("para one\n\npara two\n\npara three")
        self.assertEqual(e, 'para one\n\npara two')

    def test_middle_of_para(self):
        e = get_excerpt("some text\n<!-- split -->\nmore text")
        self.assertEqual(e, 'some text')

    def test_middle_of_line(self):
        e = get_excerpt("some text <!-- split --> more text")
        self.assertEqual(e, "some text <!-- split --> more text")

try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = None


@skipUnless(introspector, 'South is not installed')
class SouthFreezingTests(TestCase):
    def test_introspector_adds_no_excerpt_field(self):
        mf = Article._meta.get_field('body')
        args, kwargs = introspector(mf)
        self.assertEqual(kwargs['no_excerpt_field'], 'True')

    def test_no_excerpt_field_works(self):
        from .models import NoRendered
        with self.assertRaises(FieldDoesNotExist):
            NoRendered._meta.get_field('_body_excerpt')

    def test_status_field_no_check_for_status(self):
        sf = StatusFieldDefaultFilled._meta.get_field('status')
        args, kwargs = introspector(sf)
        self.assertEqual(kwargs['no_check_for_status'], 'True')
