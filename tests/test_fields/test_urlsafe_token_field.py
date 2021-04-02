from unittest.mock import Mock

from django.db.models import NOT_PROVIDED
from django.test import TestCase

from model_utils.fields import UrlsafeTokenField


class UrlsaftTokenFieldTests(TestCase):
    def test_editable_default(self):
        field = UrlsafeTokenField()
        self.assertFalse(field.editable)

    def test_editable(self):
        field = UrlsafeTokenField(editable=True)
        self.assertTrue(field.editable)

    def test_max_length_default(self):
        field = UrlsafeTokenField()
        self.assertEqual(field.max_length, 128)

    def test_max_length(self):
        field = UrlsafeTokenField(max_length=256)
        self.assertEqual(field.max_length, 256)

    def test_factory_default(self):
        field = UrlsafeTokenField()
        self.assertIsNone(field._factory)

    def test_factory_not_callable(self):
        with self.assertRaises(TypeError):
            UrlsafeTokenField(factory='INVALID')

    def test_get_default(self):
        field = UrlsafeTokenField()
        value = field.get_default()
        self.assertEqual(len(value), field.max_length)

    def test_get_default_with_non_default_max_length(self):
        field = UrlsafeTokenField(max_length=64)
        value = field.get_default()
        self.assertEqual(len(value), 64)

    def test_get_default_with_factory(self):
        token = 'SAMPLE_TOKEN'
        factory = Mock(return_value=token)
        field = UrlsafeTokenField(factory=factory)
        value = field.get_default()

        self.assertEqual(value, token)
        factory.assert_called_once_with(field.max_length)

    def test_no_default_param(self):
        field = UrlsafeTokenField(default='DEFAULT')
        self.assertIs(field.default, NOT_PROVIDED)

    def test_deconstruct(self):
        def test_factory():
            pass
        instance = UrlsafeTokenField(factory=test_factory)
        name, path, args, kwargs = instance.deconstruct()
        new_instance = UrlsafeTokenField(*args, **kwargs)
        self.assertIs(instance._factory, new_instance._factory)
        self.assertIs(test_factory, new_instance._factory)
