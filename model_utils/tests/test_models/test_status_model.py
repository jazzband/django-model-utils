from datetime import datetime

from freezegun import freeze_time

from django.test.testcases import TestCase

from model_utils.tests.models import Status, StatusPlainTuple


class StatusModelTests(TestCase):
    def setUp(self):
        self.model = Status
        self.on_hold = Status.STATUS.on_hold
        self.active = Status.STATUS.active

    def test_created(self):
        with freeze_time(datetime(2016, 1, 1)):
            c1 = self.model.objects.create()
        self.assertTrue(c1.status_changed, datetime(2016, 1, 1))

        c2 = self.model.objects.create()
        self.assertEqual(self.model.active.count(), 2)
        self.assertEqual(self.model.deleted.count(), 0)

    def test_modification(self):
        t1 = self.model.objects.create()
        date_created = t1.status_changed
        t1.status = self.on_hold
        t1.save()
        self.assertEqual(self.model.active.count(), 0)
        self.assertEqual(self.model.on_hold.count(), 1)
        self.assertTrue(t1.status_changed > date_created)
        date_changed = t1.status_changed
        t1.save()
        self.assertEqual(t1.status_changed, date_changed)
        date_active_again = t1.status_changed
        t1.status = self.active
        t1.save()
        self.assertTrue(t1.status_changed > date_active_again)


class StatusModelPlainTupleTests(StatusModelTests):
    def setUp(self):
        self.model = StatusPlainTuple
        self.on_hold = StatusPlainTuple.STATUS[2][0]
        self.active = StatusPlainTuple.STATUS[0][0]
