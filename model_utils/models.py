from __future__ import unicode_literals

import django
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction, router
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext_lazy as _

from model_utils.fields import (
    AutoCreatedField,
    AutoLastModifiedField,
    StatusField,
    MonitorField,
    UUIDField,
)
from model_utils.managers import (
    QueryManager,
    SoftDeletableManager,
)

if django.VERSION >= (1, 9, 0):
    from django.db.models.functions import Now
    now = Now()
else:
    from django.utils.timezone import now


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

    if django.VERSION >= (1, 10):
        # First, get current manager name...
        default_manager = sender._meta.default_manager

    for value, display in getattr(sender, 'STATUS', ()):
        if _field_exists(sender, value):
            raise ImproperlyConfigured(
                "StatusModel: Model '%s' has a field named '%s' which "
                "conflicts with a status of the same name."
                % (sender.__name__, value)
            )
        sender.add_to_class(value, QueryManager(status=value))

    if django.VERSION >= (1, 10):
        # ...then, put it back, as add_to_class is modifying the default manager!
        sender._meta.default_manager_name = default_manager.name


def add_timeframed_query_manager(sender, **kwargs):
    """
    Add a QueryManager for a specific timeframe.

    """
    if not issubclass(sender, TimeFramedModel):
        return
    if _field_exists(sender, 'timeframed'):
        raise ImproperlyConfigured(
            "Model '%s' has a field named 'timeframed' "
            "which conflicts with the TimeFramedModel manager."
            % sender.__name__
        )
    sender.add_to_class('timeframed', QueryManager(
        (models.Q(start__lte=now) | models.Q(start__isnull=True)) &
        (models.Q(end__gte=now) | models.Q(end__isnull=True))
    ))


models.signals.class_prepared.connect(add_status_query_managers)
models.signals.class_prepared.connect(add_timeframed_query_manager)


def _field_exists(model_class, field_name):
    return field_name in [f.attname for f in model_class._meta.local_fields]


class SoftDeletableModel(models.Model):
    """
    An abstract base class model with a ``is_removed`` field that
    marks entries that are not going to be used anymore, but are
    kept in db for any reason.
    Default manager returns only not-removed entries.
    """
    is_removed = models.BooleanField(default=False)

    class Meta:
        abstract = True

    objects = SoftDeletableManager()
    all_objects = models.Manager()

    def delete(self, using=None, soft=True, *args, **kwargs):
        """
        Soft delete object (set its ``is_removed`` field to True).
        Actually delete object if setting ``soft`` to False.
        """
        if soft:
            self.is_removed = True
            self.save(using=using)
        else:
            return super(SoftDeletableModel, self).delete(using=using, *args, **kwargs)


class UUIDModel(models.Model):
    """
    This abstract base class provides id field on any model that inherits from it
    which will be the primary key.
    """
    id = UUIDField(
        primary_key=True,
        version=4,
        editable=False,
    )

    class Meta:
        abstract = True


class SaveSignalHandlingModel(models.Model):
    """
    An abstract base class model to pass a parameter ``signals_to_disable``
    to ``save`` method in order to disable signals
    """
    class Meta:
        abstract = True

    def save(self, signals_to_disable=None, *args, **kwargs):
        """
        Add an extra parameters to hold which signals to disable
        If empty, nothing will change
        """

        self.signals_to_disable = signals_to_disable or []

        super(SaveSignalHandlingModel, self).save(*args, **kwargs)

    def save_base(self, raw=False, force_insert=False,
                  force_update=False, using=None, update_fields=None):
        """
        Copied from base class for a minor change.
        This is an ugly overwriting but since Django's ``save_base`` method
        does not differ between versions 1.8 and 1.10,
        that way of implementing wouldn't harm the flow
        """
        using = using or router.db_for_write(self.__class__, instance=self)
        assert not (force_insert and (force_update or update_fields))
        assert update_fields is None or len(update_fields) > 0
        cls = origin = self.__class__

        if cls._meta.proxy:
            cls = cls._meta.concrete_model
        meta = cls._meta
        if not meta.auto_created and not 'pre_save' in self.signals_to_disable:
            pre_save.send(
                sender=origin, instance=self, raw=raw, using=using,
                update_fields=update_fields,
            )
        with transaction.atomic(using=using, savepoint=False):
            if not raw:
                self._save_parents(cls, using, update_fields)
            updated = self._save_table(raw, cls, force_insert, force_update, using, update_fields)

        self._state.db = using
        self._state.adding = False

        if not meta.auto_created and not 'post_save' in self.signals_to_disable:
            post_save.send(
                sender=origin, instance=self, created=(not updated),
                update_fields=update_fields, raw=raw, using=using,
            )

        # Empty the signals in case it might be used somewhere else in future
        self.signals_to_disable = []
