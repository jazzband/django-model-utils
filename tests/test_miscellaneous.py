from __future__ import unicode_literals

from django.core.management import call_command
from django.test import TestCase

from model_utils.fields import get_excerpt


class MigrationsTests(TestCase):
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
