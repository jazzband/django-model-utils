from django.test import TestCase

from tests.models import CustomNotPrimaryUUIDModel, CustomUUIDModel


class UUIDFieldTests(TestCase):

    def test_uuid_model_with_uuid_field_as_primary_key(self):
        instance = CustomUUIDModel()
        instance.save()
        self.assertEqual(instance.id.__class__.__name__, 'UUID')
        self.assertEqual(instance.id, instance.pk)

    def test_uuid_model_with_uuid_field_as_not_primary_key(self):
        instance = CustomNotPrimaryUUIDModel()
        instance.save()
        self.assertEqual(instance.uuid.__class__.__name__, 'UUID')
        self.assertNotEqual(instance.uuid, instance.pk)
