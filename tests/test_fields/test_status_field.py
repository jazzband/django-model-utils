from __future__ import annotations

from django.test import TestCase

from model_utils.fields import StatusField
from tests.models import (
    Article,
    StatusFieldChoicesName,
    StatusFieldDefaultFilled,
    StatusFieldDefaultNotFilled,
)


class StatusFieldTests(TestCase):

    def test_status_with_default_filled(self) -> None:
        instance = StatusFieldDefaultFilled()
        self.assertEqual(instance.status, instance.STATUS.yes)

    def test_status_with_default_not_filled(self) -> None:
        instance = StatusFieldDefaultNotFilled()
        self.assertEqual(instance.status, instance.STATUS.no)

    def test_no_check_for_status(self) -> None:
        field = StatusField(no_check_for_status=True)
        # this model has no STATUS attribute, so checking for it would error
        field.prepare_class(Article)

    def test_get_status_display(self) -> None:
        instance = StatusFieldDefaultFilled()
        self.assertEqual(instance.get_status_display(), "Yes")

    def test_choices_name(self) -> None:
        StatusFieldChoicesName()
