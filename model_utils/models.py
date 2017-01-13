from __future__ import unicode_literals

from django.db import models, transaction
from django.template.defaultfilters import slugify
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import now

from model_utils.managers import QueryManager
from model_utils.fields import AutoCreatedField, AutoLastModifiedField, \
    StatusField, MonitorField


class TitleModel(models.Model):
    """
    For good measure
    """
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class TitleSlugModel(TitleModel):
    """
    An abstract base class model that provides a ``title``
    and ``slug`` fields
    """
    slug = models.SlugField(max_length=105, unique=True) # Longer if it tacks on integer

    SLUG_MAX_RETRIES = 5 # How many integrity errors before failing

    def generate_slug(self):
        return slugify(self.name)

    def increment_slug(self, slug):
        """
        What to do when the slug is already found in the table

        Defaults to ordinary counter appending, but you may
        want to use a date or some other token
        """
        tries = getattr(self, '_slug_increment', 1)
        self._slug_increment = tries + 1
        return slugify('%s-%s' % (slug, self._slug_increment))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_slug()

        """
        Its not enough to check for the slug first because in rare
        cases it can be created between the get and the save below.

        Below, we attempt to save a unique slug but sometimes that
        doesn't go well. In that case, we retry on integrityerror a
        few times, incrementing our slug along the way.

        since our integrityerror might have other causes besides the slug,
        we don't let this runaway indefinitely and eventually raise

        If below fails, you must find another way of assigning
        a slug before calling model save()

        """

        tries = self.SLUG_MAX_RETRIES
        while True:
            try:
                with transaction.atomic():
                    super(TitleSlugModel, self).save(*args, **kwargs)
                    break
            except IntegrityError, e:
                if tries == 0:
                    raise

                tries = tries - 1
                self.slug = self.increment_slug(self.generate_slug())

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
        if _field_exists(sender, value):
            raise ImproperlyConfigured(
                "StatusModel: Model '%s' has a field named '%s' which "
                "conflicts with a status of the same name."
                % (sender.__name__, value)
            )
        sender.add_to_class(value, QueryManager(status=value))


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
