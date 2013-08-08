import json

from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


class SimpleJSONField(models.TextField):

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return json.loads(value)
        except ValueError:
            pass

        return value

    def get_db_prep_save(self, value, connection):
        if value == "":
            return None

        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        return super(SimpleJSONField, self).get_db_prep_save(value, connection)
