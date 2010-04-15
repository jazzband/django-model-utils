from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import FieldDoesNotExist

from model_utils.managers import QueryManager
from model_utils.fields import AutoCreatedField, AutoLastModifiedField, \
    StatusField, StatusModifiedField

class InheritanceCastModel(models.Model):
    """
    An abstract base class that provides a ``real_type`` FK to ContentType.

    For use in trees of inherited models, to be able to downcast
    parent instances to their child types.

    """
    real_type = models.ForeignKey(ContentType, editable=False, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.real_type = self._get_real_type()
        super(InheritanceCastModel, self).save(*args, **kwargs)

    def _get_real_type(self):
        return ContentType.objects.get_for_model(type(self))

    def cast(self):
        return self.real_type.get_object_for_this_type(pk=self.pk)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.

    """
    created = AutoCreatedField(_('created'))
    modified = AutoLastModifiedField(_('modified'))

    class Meta:
        abstract = True


class TimeFramedModel(models.Model):
    """
    An abstract base class model that provides ``start``
    and ``end`` fields to record a timeframe.

    """
    start = models.DateTimeField(_('start'), null=True, blank=True)
    end = models.DateTimeField(_('end'), null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(TimeFramedModel, self).__init__(*args, **kwargs)
        try:
            self._meta.get_field('timeframed')
            raise ValueError("Model %s has a field named 'timeframed' and "
                             "conflicts with a manager." % self.__name__)
        except FieldDoesNotExist:
            pass
        self.__class__.add_to_class('timeframed', QueryManager(
            (models.Q(start__lte=datetime.now()) | models.Q(start__isnull=True)) &
            (models.Q(end__gte=datetime.now()) | models.Q(end__isnull=True))
        ))

    class Meta:
        abstract = True

class StatusModel(models.Model):
    """
    An abstract base class model that provides self-updating
    status fields like ``deleted`` and ``restored``.

    """
    status = StatusField(_('status'))
    status_date = StatusModifiedField(_('status date'))

    def __init__(self, *args, **kwargs):
        super(StatusModel, self).__init__(*args, **kwargs)
        for value, name in getattr(self, 'STATUS', ()):
            try:
                self._meta.get_field(name)
                raise ValueError("Model %s has a field named '%s' and "
                                 "conflicts with a status."
                                 % (self.__name__, name))
            except FieldDoesNotExist:
                pass
            self.__class__.add_to_class(value, QueryManager(status=value))

    def __unicode__(self):
        return self.get_status_display()

    class Meta:
        abstract = True

