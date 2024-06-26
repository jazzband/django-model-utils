from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from model_utils.managers import QueryManager
from model_utils.models import StatusModel
from tests.models import StatusManagerAdded


class StatusManagerAddedTests(TestCase):
    def test_manager_available(self) -> None:
        self.assertTrue(isinstance(StatusManagerAdded.active, QueryManager))

    def test_conflict_error(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(StatusModel):
                STATUS = (
                    ('active', 'Is Active'),
                    ('deleted', 'Is Deleted'),
                )
                active = models.BooleanField()
