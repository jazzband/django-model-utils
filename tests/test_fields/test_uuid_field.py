from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.db.migrations.state import ModelState
from django.db.migrations.writer import MigrationWriter
from django.test import TestCase

from model_utils.fields import UUIDField
from tests.models import CustomNotPrimaryUUIDModel


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

    def test_deconstruct(self) -> None:
        for primary_key in (None, True, False):
            with self.subTest(primary_key=primary_key):
                instance = UUIDField() if primary_key is None else UUIDField(primary_key=primary_key)
                name, path, args, kwargs = instance.deconstruct()
                self.assertIsNone(name)
                self.assertEqual(path, 'model_utils.fields.UUIDField')
                self.assertEqual(args, [])
                self.assertEqual(kwargs, {
                    'primary_key': primary_key is not False,
                    'editable': False,
                    'default': uuid.uuid4,
                })
                new_instance = UUIDField(*args, **kwargs)
                self.assertEqual(new_instance.primary_key, primary_key is not False)
                self.assertFalse(new_instance.editable)
                self.assertIs(new_instance.default, uuid.uuid4)
                self.assertEqual(new_instance.get_default().version, 4)

    def test_clone(self) -> None:
        instance = UUIDField(
            primary_key=False,
            default=uuid.uuid1,
            editable=False,
            serialize=False,
            unique=True,
            db_column='external_uuid',
        )
        # Field.clone() is not declared in django-stubs.
        assert hasattr(instance, 'clone')
        new_instance = instance.clone()
        assert isinstance(new_instance, UUIDField)
        self.assertIsNot(new_instance, instance)
        self.assertFalse(new_instance.primary_key)
        self.assertIs(new_instance.default, uuid.uuid1)
        self.assertEqual(new_instance.get_default().version, 1)
        self.assertFalse(new_instance.editable)
        self.assertFalse(new_instance.deconstruct()[3]['serialize'])
        self.assertTrue(new_instance.unique)
        self.assertEqual(new_instance.db_column, 'external_uuid')

    def test_migration_serialization(self) -> None:
        state = ModelState.from_model(CustomNotPrimaryUUIDModel)
        serialized, imports = MigrationWriter.serialize(state.fields['uuid'])
        self.assertEqual(
            serialized,
            'model_utils.fields.UUIDField(default=uuid.uuid4, '
            'editable=False, primary_key=False)',
        )
        self.assertEqual(imports, {'import model_utils.fields', 'import uuid'})
        self.assertEqual(
            [name for name, field in state.fields.items() if field.primary_key],
            ['id'],
        )
