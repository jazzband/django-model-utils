from __future__ import annotations

from django.test import TestCase

from tests.models import CustomSoftDelete


class CustomSoftDeleteManagerTests(TestCase):

    def test_custom_manager_empty(self) -> None:
        qs = CustomSoftDelete.available_objects.only_read()
        self.assertEqual(qs.count(), 0)

    def test_custom_qs_empty(self) -> None:
        qs = CustomSoftDelete.available_objects.all().only_read()
        self.assertEqual(qs.count(), 0)

    def test_is_read(self) -> None:
        for is_read in [True, False, True, False]:
            CustomSoftDelete.available_objects.create(is_read=is_read)
        qs = CustomSoftDelete.available_objects.only_read()
        self.assertEqual(qs.count(), 2)

    def test_is_read_removed(self) -> None:
        for is_read, is_removed in [(True, True), (True, False), (False, False), (False, True)]:
            CustomSoftDelete.available_objects.create(is_read=is_read, is_removed=is_removed)
        qs = CustomSoftDelete.available_objects.only_read()
        self.assertEqual(qs.count(), 1)
