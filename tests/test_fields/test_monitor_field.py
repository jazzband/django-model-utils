from datetime import datetime

from django.test import TestCase
from freezegun import freeze_time

from model_utils.fields import MonitorField
from tests.models import DoubleMonitored, Monitored, MonitorWhen, MonitorWhenEmpty


class MonitorFieldTests(TestCase):
    def setUp(self):
        with freeze_time(datetime(2016, 1, 1, 10, 0, 0)):
            self.instance = Monitored(name='Charlie')
            self.created = self.instance.name_changed

    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed(self):
        with freeze_time(datetime(2016, 1, 1, 12, 0, 0)):
            self.instance.name = 'Maria'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0))

    def test_double_save(self):
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)

    def test_no_monitor_arg(self):
        with self.assertRaises(TypeError):
            MonitorField()


class MonitorWhenFieldTests(TestCase):
    """
    Will record changes only when name is 'Jose' or 'Maria'
    """
    def setUp(self):
        with freeze_time(datetime(2016, 1, 1, 10, 0, 0)):
            self.instance = MonitorWhen(name='Charlie')
            self.created = self.instance.name_changed

    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Jose(self):
        with freeze_time(datetime(2016, 1, 1, 12, 0, 0)):
            self.instance.name = 'Jose'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0))

    def test_save_changed_to_Maria(self):
        with freeze_time(datetime(2016, 1, 1, 12, 0, 0)):
            self.instance.name = 'Maria'
            self.instance.save()
        self.assertEqual(self.instance.name_changed, datetime(2016, 1, 1, 12, 0, 0))

    def test_save_changed_to_Pedro(self):
        self.instance.name = 'Pedro'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_double_save(self):
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)


class MonitorWhenEmptyFieldTests(TestCase):
    """
    Monitor should never be updated id when is an empty list.
    """
    def setUp(self):
        self.instance = MonitorWhenEmpty(name='Charlie')
        self.created = self.instance.name_changed

    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Jose(self):
        self.instance.name = 'Jose'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)

    def test_save_changed_to_Maria(self):
        self.instance.name = 'Maria'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


class MonitorDoubleFieldTests(TestCase):

    def setUp(self):
        DoubleMonitored.objects.create(name='Charlie', name2='Charlie2')

    def test_recursion_error_with_only(self):
        # Any field passed to only() is generating a recursion error
        list(DoubleMonitored.objects.only('id'))

    def test_recursion_error_with_defer(self):
        # Only monitored fields passed to defer() are failing
        list(DoubleMonitored.objects.defer('name'))

    def test_monitor_still_works_with_deferred_fields_filtered_out_of_save_initial(self):
        obj = DoubleMonitored.objects.defer('name').get(name='Charlie')
        with freeze_time("2016-12-01"):
            obj.name = 'Charlie2'
            obj.save()
        self.assertEqual(obj.name_changed, datetime(2016, 12, 1))
