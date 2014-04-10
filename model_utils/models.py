from __future__ import unicode_literals
from os import path

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now

from model_utils.managers import QueryManager
from model_utils.fields import AutoCreatedField, AutoLastModifiedField, \
    StatusField, MonitorField


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

    class Meta:
        abstract = True

class StatusModel(models.Model):
    """
    An abstract base class model with a ``status`` field that
    automatically uses a ``STATUS`` class attribute of choices, a
    ``status_changed`` date-time field that records when ``status``
    was last modified, and an automatically-added manager for each
    status that returns objects with that status only.

    """
    status = StatusField(_('status'))
    status_changed = MonitorField(_('status changed'), monitor='status')

    class Meta:
        abstract = True

def add_status_query_managers(sender, **kwargs):
    """
    Add a Querymanager for each status item dynamically.

    """
    if not issubclass(sender, StatusModel):
        return
    for value, display in getattr(sender, 'STATUS', ()):
        try:
            sender._meta.get_field(value)
            raise ImproperlyConfigured("StatusModel: Model '%s' has a field "
                                       "named '%s' which conflicts with a "
                                       "status of the same name."
                                       % (sender.__name__, value))
        except FieldDoesNotExist:
            pass
        sender.add_to_class(value, QueryManager(status=value))

def add_timeframed_query_manager(sender, **kwargs):
    """
    Add a QueryManager for a specific timeframe.

    """
    if not issubclass(sender, TimeFramedModel):
        return
    try:
        sender._meta.get_field('timeframed')
        raise ImproperlyConfigured("Model '%s' has a field named "
                                   "'timeframed' which conflicts with "
                                   "the TimeFramedModel manager."
                                   % sender.__name__)
    except FieldDoesNotExist:
        pass
    sender.add_to_class('timeframed', QueryManager(
        (models.Q(start__lte=now) | models.Q(start__isnull=True)) &
        (models.Q(end__gte=now) | models.Q(end__isnull=True))
    ))


models.signals.class_prepared.connect(add_status_query_managers)
models.signals.class_prepared.connect(add_timeframed_query_manager)


def random_filename(directory='', random_function=None):
    """Returns a function that generates random filenames for file
    uploads. The new filename keeps the extension from the original
    upload.

    The default ``random_function`` is uuid.uuid4 which also will
    ensure that the filename is reasonably unique.

    Args:
      directory: The directory the file should be uploaded to. Default: ''
      random_function: A function that takes a filename as an argument
        to generate a unique filename. The file extension will be added
        to the value returned from this function. Default: uuid.uuid4

    Returns: a function that can be used with Django's ``FileField``.

    """
    if not random_function:
        from uuid import uuid4
        random_function = lambda _: uuid4()

    def random_name(instance, filename):
        return path.join(directory,
                         '{0}{1}'.format(random_function(filename),
                                         path.splitext(filename)[1]))

    return random_name
