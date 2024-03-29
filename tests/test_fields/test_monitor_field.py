from __future__ import annotations

from datetime import datetime, timezone

import time_machine
from django.test import TestCase

from model_utils.fields import MonitorField
from tests.models import DoubleMonitored, Monitored, MonitorWhen, MonitorWhenEmpty


class MonitorFieldTests(TestCase):
    def setUp(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, 10, 0, 0, tzinfo=timezone.utc)):
            self.instance = Monitored(name='Charlie')
            self.created = self.instance.name_changed

    def test_save_no_change(self) -> None:
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc)):
            self.instance.name = 'Maria'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc))

    def test_double_save(self) -> None:
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)

    def test_no_monitor_arg(self) -> None:
        with self.assertRaises(TypeError):
            MonitorField()  # type: ignore[call-arg]

    def test_monitor_default_is_none_when_nullable(self) -> None:
        self.assertIsNone(self.instance.name_changed_nullable)
        expected_datetime = datetime(2022, 1, 18, 12, 0, 0, tzinfo=timezone.utc)

        self.instance.name = "Jose"
        with time_machine.travel(expected_datetime, tick=False):
            self.instance.save()

        self.assertEqual(self.instance.name_changed_nullable, expected_datetime)


class MonitorWhenFieldTests(TestCase):
    """
    Will record changes only when name is 'Jose' or 'Maria'
    """
    def setUp(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, 10, 0, 0, tzinfo=timezone.utc)):
            self.instance = MonitorWhen(name='Charlie')
            self.created = self.instance.name_changed

    def test_save_no_change(self) -> None:
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Jose(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc)):
            self.instance.name = 'Jose'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc))

    def test_save_changed_to_Maria(self) -> None:
        with time_machine.travel(datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc)):
            self.instance.name = 'Maria'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0, tzinfo=timezone.utc))

    def test_save_changed_to_Pedro(self) -> None:
        self.instance.name = 'Pedro'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_double_save(self) -> None:
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)


class MonitorWhenEmptyFieldTests(TestCase):
    """
    Monitor should never be updated id when is an empty list.
    """
    def setUp(self) -> None:
        self.instance = MonitorWhenEmpty(name='Charlie')
        self.created = self.instance.name_changed

    def test_save_no_change(self) -> None:
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Jose(self) -> None:
        self.instance.name = 'Jose'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Maria(self) -> None:
        self.instance.name = 'Maria'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


class MonitorDoubleFieldTests(TestCase):

    def setUp(self) -> None:
        DoubleMonitored.objects.create(name='Charlie', name2='Charlie2')

    def test_recursion_error_with_only(self) -> None:
        # Any field passed to only() is generating a recursion error
        list(DoubleMonitored.objects.only('id'))

    def test_recursion_error_with_defer(self) -> None:
        # Only monitored fields passed to defer() are failing
        list(DoubleMonitored.objects.defer('name'))

    def test_monitor_still_works_with_deferred_fields_filtered_out_of_save_initial(self) -> None:
        obj = DoubleMonitored.objects.defer('name').get(name='Charlie')
        with time_machine.travel(datetime(2016, 12, 1, tzinfo=timezone.utc)):
            obj.name = 'Charlie2'
            obj.save()
        self.assertEqual(obj.name_changed, datetime(2016, 12, 1, tzinfo=timezone.utc))
