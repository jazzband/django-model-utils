from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.test import TestCase

from model_utils.fields import UUIDField


class UUIDFieldTests(TestCase):

    def test_uuid_version_default(self) -> None:
        instance = UUIDField()
        self.assertEqual(instance.default, uuid.uuid4)

    def test_uuid_version_1(self) -> None:
        instance = UUIDField(version=1)
        self.assertEqual(instance.default, uuid.uuid1)

    def test_uuid_version_2_error(self) -> None:
        self.assertRaises(ValidationError, UUIDField, 'version', 2)

    def test_uuid_version_3(self) -> None:
        instance = UUIDField(version=3)
        self.assertEqual(instance.default, uuid.uuid3)

    def test_uuid_version_4(self) -> None:
        instance = UUIDField(version=4)
        self.assertEqual(instance.default, uuid.uuid4)

    def test_uuid_version_5(self) -> None:
        instance = UUIDField(version=5)
        self.assertEqual(instance.default, uuid.uuid5)

    def test_uuid_version_bellow_min(self) -> None:
        self.assertRaises(ValidationError, UUIDField, 'version', 0)

    def test_uuid_version_above_max(self) -> None:
        self.assertRaises(ValidationError, UUIDField, 'version', 6)
