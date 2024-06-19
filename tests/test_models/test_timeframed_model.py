from __future__ import annotations

from datetime import datetime, timedelta

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from model_utils.managers import QueryManager
from model_utils.models import TimeFramedModel
from tests.models import TimeFrame, TimeFrameManagerAdded


class TimeFramedModelTests(TestCase):
    def setUp(self) -> None:
        self.now = datetime.now()

    def test_not_yet_begun(self) -> None:
        TimeFrame.objects.create(start=self.now + timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 0)

    def test_finished(self) -> None:
        TimeFrame.objects.create(end=self.now - timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 0)

    def test_no_end(self) -> None:
        TimeFrame.objects.create(start=self.now - timedelta(days=10))
        self.assertEqual(TimeFrame.timeframed.count(), 1)

    def test_no_start(self) -> None:
        TimeFrame.objects.create(end=self.now + timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 1)

    def test_within_range(self) -> None:
        TimeFrame.objects.create(start=self.now - timedelta(days=1),
                                 end=self.now + timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 1)


class TimeFrameManagerAddedTests(TestCase):
    def test_manager_available(self) -> None:
        self.assertTrue(isinstance(TimeFrameManagerAdded.timeframed, QueryManager))

    def test_conflict_error(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(TimeFramedModel):
                timeframed = models.BooleanField()
