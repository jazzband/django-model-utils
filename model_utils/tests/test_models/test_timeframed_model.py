from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from model_utils.managers import QueryManager
from model_utils.models import TimeFramedModel
from model_utils.tests.models import TimeFrame, TimeFrameManagerAdded


class TimeFramedModelTests(TestCase):
    def setUp(self):
        self.now = datetime.now()

    def test_not_yet_begun(self):
        TimeFrame.objects.create(start=self.now + timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 0)

    def test_finished(self):
        TimeFrame.objects.create(end=self.now - timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 0)

    def test_no_end(self):
        TimeFrame.objects.create(start=self.now - timedelta(days=10))
        self.assertEqual(TimeFrame.timeframed.count(), 1)

    def test_no_start(self):
        TimeFrame.objects.create(end=self.now + timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 1)

    def test_within_range(self):
        TimeFrame.objects.create(start=self.now - timedelta(days=1),
                                 end=self.now + timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 1)


class TimeFrameManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assertTrue(isinstance(TimeFrameManagerAdded.timeframed, QueryManager))

    def test_conflict_error(self):
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(TimeFramedModel):
                timeframed = models.BooleanField()
