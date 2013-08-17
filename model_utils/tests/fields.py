from django.db import models

try:
    unicode()
    str_class = basestring
except NameError:
    str_class = str

def with_metaclass(meta, base=object):
    return meta("NewBase", (base,), {})


class MutableField(with_metaclass(models.SubfieldBase, models.TextField)):

    def to_python(self, value):
        if value == '':
            return None

        try:
            if isinstance(value, str_class):
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
