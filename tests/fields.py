import django
from django.db import models
from django.utils.six import with_metaclass, string_types


def mutable_from_db(value):
    if value == '':
        return None
    try:
        if isinstance(value, string_types):
            return [int(i) for i in value.split(',')]
    except ValueError:
        pass
    return value


def mutable_to_db(value):
    if value is None:
        return ''
    if isinstance(value, list):
        value = ','.join((str(i) for i in value))
    return str(value)


if django.VERSION >= (1, 9, 0):
    class MutableField(models.TextField):
        def to_python(self, value):
            return mutable_from_db(value)

        def from_db_value(self, value, expression, connection, context):
            return mutable_from_db(value)

        def get_db_prep_save(self, value, connection):
            value = super(MutableField, self).get_db_prep_save(value, connection)
            return mutable_to_db(value)
else:
    class MutableField(with_metaclass(models.SubfieldBase, models.TextField)):
        def to_python(self, value):
            return mutable_from_db(value)

        def get_db_prep_save(self, value, connection):
            value = mutable_to_db(value)
            return super(MutableField, self).get_db_prep_save(value, connection)
