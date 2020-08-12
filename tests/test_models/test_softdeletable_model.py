from django.db.utils import ConnectionDoesNotExist
from django.test import TestCase

from tests.models import SoftDeletable


class SoftDeletableModelTests(TestCase):
    def test_can_only_see_not_removed_entries(self):
        SoftDeletable.available_objects.create(name='a', is_removed=True)
        SoftDeletable.available_objects.create(name='b', is_removed=False)

        queryset = SoftDeletable.available_objects.all()

        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].name, 'b')

    def test_instance_cannot_be_fully_deleted(self):
        instance = SoftDeletable.available_objects.create(name='a')

        instance.delete()

        self.assertEqual(SoftDeletable.available_objects.count(), 0)
        self.assertEqual(SoftDeletable.all_objects.count(), 1)

    def test_instance_cannot_be_fully_deleted_via_queryset(self):
        SoftDeletable.available_objects.create(name='a')

        SoftDeletable.available_objects.all().delete()

        self.assertEqual(SoftDeletable.available_objects.count(), 0)
        self.assertEqual(SoftDeletable.all_objects.count(), 1)

    def test_delete_instance_no_connection(self):
        obj = SoftDeletable.available_objects.create(name='a')

        self.assertRaises(ConnectionDoesNotExist, obj.delete, using='other')

    def test_instance_purge(self):
        instance = SoftDeletable.available_objects.create(name='a')

        instance.delete(soft=False)

        self.assertEqual(SoftDeletable.available_objects.count(), 0)
        self.assertEqual(SoftDeletable.all_objects.count(), 0)

    def test_instance_purge_no_connection(self):
        instance = SoftDeletable.available_objects.create(name='a')

        self.assertRaises(ConnectionDoesNotExist, instance.delete,
                          using='other', soft=False)

    def test_deprecation_warning(self):
        self.assertWarns(DeprecationWarning, SoftDeletable.objects.all)
