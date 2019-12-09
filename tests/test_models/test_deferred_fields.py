from django.test import TestCase

from tests.models import ModelWithCustomDescriptor


class CustomDescriptorTests(TestCase):
    def setUp(self):
        self.instance = ModelWithCustomDescriptor.objects.create(
            custom_field='1',
            tracked_custom_field='1',
            regular_field=1,
            tracked_regular_field=1,
        )

    def test_custom_descriptor_works(self):
        instance = self.instance
        self.assertEqual(instance.custom_field, '1')
        self.assertEqual(instance.__dict__['custom_field'], 1)
        self.assertEqual(instance.regular_field, 1)
        instance.custom_field = 2
        self.assertEqual(instance.custom_field, '2')
        self.assertEqual(instance.__dict__['custom_field'], 2)
        instance.save()
        instance = ModelWithCustomDescriptor.objects.get(pk=instance.pk)
        self.assertEqual(instance.custom_field, '2')
        self.assertEqual(instance.__dict__['custom_field'], 2)

    def test_deferred(self):
        instance = ModelWithCustomDescriptor.objects.only('id').get(
            pk=self.instance.pk)
        self.assertIn('custom_field', instance.get_deferred_fields())
        self.assertEqual(instance.custom_field, '1')
        self.assertNotIn('custom_field', instance.get_deferred_fields())
        self.assertEqual(instance.regular_field, 1)
        self.assertEqual(instance.tracked_custom_field, '1')
        self.assertEqual(instance.tracked_regular_field, 1)

        self.assertFalse(instance.tracker.has_changed('tracked_custom_field'))
        self.assertFalse(instance.tracker.has_changed('tracked_regular_field'))

        instance.tracked_custom_field = 2
        instance.tracked_regular_field = 2
        self.assertTrue(instance.tracker.has_changed('tracked_custom_field'))
        self.assertTrue(instance.tracker.has_changed('tracked_regular_field'))
        instance.save()

        instance = ModelWithCustomDescriptor.objects.get(pk=instance.pk)
        self.assertEqual(instance.custom_field, '1')
        self.assertEqual(instance.regular_field, 1)
        self.assertEqual(instance.tracked_custom_field, '2')
        self.assertEqual(instance.tracked_regular_field, 2)

        instance = ModelWithCustomDescriptor.objects.only('id').get(pk=instance.pk)
        instance.tracked_custom_field = 3
        self.assertEqual(instance.tracked_custom_field, '3')
        self.assertTrue(instance.tracker.has_changed('tracked_custom_field'))
        del instance.tracked_custom_field
        self.assertEqual(instance.tracked_custom_field, '2')
        self.assertFalse(instance.tracker.has_changed('tracked_custom_field'))
