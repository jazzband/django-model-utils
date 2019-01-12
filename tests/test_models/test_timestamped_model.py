from __future__ import unicode_literals

from datetime import datetime

from freezegun import freeze_time

from django.test import TestCase

from tests.models import TimeStamp


class TimeStampedModelTests(TestCase):
    def test_created(self):
        with freeze_time(datetime(2016, 1, 1)):
            t1 = TimeStamp.objects.create()
        self.assertEqual(t1.created, datetime(2016, 1, 1))

    def test_created_sets_modified(self):
        '''
        Ensure that on creation that modifed is set exactly equal to created.
        '''
        t1 = TimeStamp.objects.create()
        self.assertEqual(t1.created, t1.modified)

    def test_modified(self):
        with freeze_time(datetime(2016, 1, 1)):
            t1 = TimeStamp.objects.create()

        with freeze_time(datetime(2016, 1, 2)):
            t1.save()

        self.assertEqual(t1.modified, datetime(2016, 1, 2))
