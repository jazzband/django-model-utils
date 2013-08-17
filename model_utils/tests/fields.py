from django.db import models
from django.utils.six import with_metaclass, string_types


class MutableField(with_metaclass(models.SubfieldBase, models.TextField)):

    def to_python(self, value):
        if value == '':
            return None

        try:
            if isinstance(value, string_types):
                return [int(i) for i in value.split(',')]
        except ValueError:
            pass

        return value

    def get_db_prep_save(self, value, connection):
        if value is None:
            return ''

        if isinstance(value, list):
            value = ','.join((str(i) for i in value))

        return super(MutableField, self).get_db_prep_save(value, connection)
