from __future__ import annotations

from datetime import datetime, timezone

import time_machine
from django.test import TestCase

from tests.models import Created


class CreatedModelTests(TestCase):
    def test_created(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, tzinfo=timezone.utc)):
            obj = Created.objects.create()
        self.assertEqual(obj.created, datetime(2016, 1, 1, tzinfo=timezone.utc))

    def test_created_is_not_changed_on_later_save(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, tzinfo=timezone.utc)):
            obj = Created.objects.create()

        with time_machine.travel(datetime(2016, 1, 2, tzinfo=timezone.utc)):
            obj.test_field = 1
            obj.save()

        self.assertEqual(obj.created, datetime(2016, 1, 1, tzinfo=timezone.utc))

    def test_overriding_created_via_object_creation(self) -> None:
        different_date = datetime(2010, 1, 1, tzinfo=timezone.utc)
        obj = Created.objects.create(created=different_date)
        self.assertEqual(obj.created, different_date)
