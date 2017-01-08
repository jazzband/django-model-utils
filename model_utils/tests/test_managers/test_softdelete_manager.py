from __future__ import unicode_literals

from django.test import TestCase

from model_utils.tests.models import CustomSoftDelete


class CustomSoftDeleteManagerTests(TestCase):

    def test_custom_manager_empty(self):
        qs = CustomSoftDelete.objects.only_read()
        self.assertEqual(qs.count(), 0)

    def test_custom_qs_empty(self):
        qs = CustomSoftDelete.objects.all().only_read()
        self.assertEqual(qs.count(), 0)

    def test_is_read(self):
        for is_read in [True, False, True, False]:
            CustomSoftDelete.objects.create(is_read=is_read)
        qs = CustomSoftDelete.objects.only_read()
        self.assertEqual(qs.count(), 2)

    def test_is_read_removed(self):
        for is_read, is_removed in [(True, True), (True, False), (False, False), (False, True)]:
            CustomSoftDelete.objects.create(is_read=is_read, is_removed=is_removed)
        qs = CustomSoftDelete.objects.only_read()
        self.assertEqual(qs.count(), 1)
