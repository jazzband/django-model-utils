from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.models import InheritanceCastModel, TimeStampedModel, StatusModel, TimeFramedModel
from model_utils.managers import QueryManager, manager_from
from model_utils.fields import SplitField, MonitorField
from model_utils import Choices

class InheritParent(InheritanceCastModel):
    pass

class InheritChild(InheritParent):
    pass

class InheritChild2(InheritParent):
    pass

class TimeStamp(TimeStampedModel):
    pass

class TimeFrame(TimeFramedModel):
    pass

class TimeFrameManagerAdded(TimeFramedModel):
    pass

class Monitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor='name')

class Status(StatusModel):
    STATUS = Choices(
        ('active', _('active')),
        ('deleted', _('deleted')),
        ('on_hold', _('on hold')),
    )

class StatusPlainTuple(StatusModel):
    STATUS = (
        ('active', _('active')),
        ('deleted', _('deleted')),
        ('on_hold', _('on hold')),
    )

class StatusManagerAdded(StatusModel):
    STATUS = (
        ('active', _('active')),
        ('deleted', _('deleted')),
        ('on_hold', _('on hold')),
    )

class Post(models.Model):
    published = models.BooleanField()
    confirmed = models.BooleanField()
    order = models.IntegerField()

    objects = models.Manager()
    public = QueryManager(published=True)
    public_confirmed = QueryManager(models.Q(published=True) &
                                    models.Q(confirmed=True))
    public_reversed = QueryManager(published=True).order_by('-order')

    class Meta:
        ordering = ('order',)

class Article(models.Model):
    title = models.CharField(max_length=50)
    body = SplitField()

class NoRendered(models.Model):
    """
    Test that the no_excerpt_field keyword arg works. This arg should
    never be used except by the South model-freezing.

    """
    body = SplitField(no_excerpt_field=True)

class AuthorMixin(object):
    def by_author(self, name):
        return self.filter(author=name)

class PublishedMixin(object):
    def published(self):
        return self.filter(published=True)

def unpublished(self):
    return self.filter(published=False)

class ByAuthorQuerySet(models.query.QuerySet, AuthorMixin):
    pass

class FeaturedManager(models.Manager):
    def get_query_set(self):
        kwargs = {}
        if hasattr(self, '_db'):
            kwargs['using'] = self._db
        return ByAuthorQuerySet(self.model, **kwargs).filter(feature=True)

class Entry(models.Model):
    author = models.CharField(max_length=20)
    published = models.BooleanField()
    feature = models.BooleanField(default=False)
    
    objects = manager_from(AuthorMixin, PublishedMixin, unpublished)
    broken = manager_from(PublishedMixin, manager_cls=FeaturedManager)
    featured = manager_from(PublishedMixin,
                            manager_cls=FeaturedManager,
                            queryset_cls=ByAuthorQuerySet)
