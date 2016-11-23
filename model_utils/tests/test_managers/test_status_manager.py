from __future__ import unicode_literals

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from model_utils.managers import QueryManager
from model_utils.models import StatusModel
from model_utils.tests.models import StatusManagerAdded


class StatusManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assertTrue(isinstance(StatusManagerAdded.active, QueryManager))

    def test_conflict_error(self):
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(StatusModel):
                STATUS = (
                    ('active', 'Is Active'),
                    ('deleted', 'Is Deleted'),
                )
                active = models.BooleanField()
