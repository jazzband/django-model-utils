from __future__ import annotations

from typing import Any

from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper


def mutable_from_db(value: object) -> Any:
    if value == '':
        return None
    try:
        if isinstance(value, (str,)):
            return [int(i) for i in value.split(',')]
    except ValueError:
        pass
    return value


def mutable_to_db(value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        value = ','.join(str(i) for i in value)
    return str(value)


class MutableField(models.TextField):
    def to_python(self, value: object) -> Any:
        return mutable_from_db(value)

    def from_db_value(self, value: object, expression: object, connection: BaseDatabaseWrapper) -> Any:
        return mutable_from_db(value)

    def get_db_prep_save(self, value: object, connection: BaseDatabaseWrapper) -> str:
        value = super().get_db_prep_save(value, connection)
        return mutable_to_db(value)
