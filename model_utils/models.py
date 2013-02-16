from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import ImproperlyConfigured, FieldError

from model_utils.managers import QueryManager
from model_utils.fields import AutoCreatedField, AutoLastModifiedField, \
    StatusField, MonitorField

try:
    from django.utils.timezone import now as now
except ImportError:
    now = datetime.now



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
    for value, name in getattr(sender, 'STATUS', ()):
        try:
            sender._meta.get_field(name)
            raise ImproperlyConfigured("StatusModel: Model '%s' has a field "
                                       "named '%s' which conflicts with a "
                                       "status of the same name."
                                       % (sender.__name__, name))
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


class ModelTracker(object):
    def __init__(self, fields=None):
        self.fields = fields

    def contribute_to_class(self, cls, name):
        self.name = name
        models.signals.class_prepared.connect(self.finalize, sender=cls)

    def finalize(self, sender, **kwargs):
        descriptor = ModelTrackerDescriptor(sender, self.name, self.fields)
        setattr(sender, self.name, descriptor)


class ModelTrackerDescriptor(object):
    def __init__(self, cls, name, fields):
        self.attname = '_%s' % name
        self.fields = fields
        if self.fields is None:
            self.fields = [field.attname for field in cls._meta.local_fields]
        models.signals.post_init.connect(self.initialize, sender=cls)

    def initialize(self, sender, instance, **kwargs):
        tracker = ModelInstanceTracker(instance, self.fields)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()
        self.patch_save(instance)

    def patch_save(self, instance):
        original_save = instance.save
        def save(**kwargs):
            ret = original_save()
            getattr(instance, self.attname).set_saved_fields()
            return ret
        setattr(instance, 'save', save)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return getattr(instance, self.attname)


class ModelInstanceTracker(object):
    def __init__(self, instance, fields):
        self.instance = instance
        self.fields = fields

    def set_saved_fields(self):
        self.saved_data = self.current_fields()

    def current_fields(self):
        return (dict((f, getattr(self.instance, f)) for f in self.fields)
                if self.instance.pk else {})

    def has_changed(self, field):
        """Returns ``True`` if field has changed from currently saved value"""
        if not self.instance.pk:
            return True
        elif field in self.saved_data:
            return self.saved_data.get(field) != getattr(self.instance, field)
        else:
            raise FieldError('field "%s" not tracked' % field)

    def previous(self, field):
        """Return currently saved value of given field"""
        return self.saved_data.get(field)

    def changed(self):
        """Returns dict of fields that changed since save (with old values)"""
        if not self.instance.pk:
            return {}
        saved = self.saved_data.iteritems()
        current = self.current_fields()
        return dict((k, v) for k, v in saved if v != current[k])
