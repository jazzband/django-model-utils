from __future__ import annotations

from django.test import TestCase

from tests.models import TrackedModelWithSpecialNamedField


class SpecialNamedFieldTests(TestCase):
    def test_model_with_instance_field(self) -> None:
        t = TrackedModelWithSpecialNamedField.objects.create(
            instance="45.55",
            name="test",
        )
        self.assertEqual(t.instance, "45.55")

        t.instance = "56.78"
        t.save()

        t.delete()
