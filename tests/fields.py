from django.db import models


def mutable_from_db(value):
    if value == '':
        return None
    try:
        if isinstance(value, (str,)):
            return [int(i) for i in value.split(',')]
    except ValueError:
        pass
    return value


def mutable_to_db(value):
    if value is None:
        return ''
    if isinstance(value, list):
        value = ','.join(str(i) for i in value)
    return str(value)


class MutableField(models.TextField):
    def to_python(self, value):
        return mutable_from_db(value)

    def from_db_value(self, value, expression, connection):
        return mutable_from_db(value)

    def get_db_prep_save(self, value, connection):
        value = super().get_db_prep_save(value, connection)
        return mutable_to_db(value)
