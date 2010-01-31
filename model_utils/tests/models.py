from django.db import models

from model_utils.models import InheritanceCastModel, TimeStampedModel
from model_utils.managers import QueryManager
from model_utils.fields import SplitField


class InheritParent(InheritanceCastModel):
    pass

class InheritChild(InheritParent):
    pass

class TimeStamp(TimeStampedModel):
    pass

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

    def __unicode__(self):
        return self.title

class NoRendered(models.Model):
    """
    Test that the no_excerpt_field keyword arg works. This arg should
    never be used except by the South model-freezing.

    """
    body = SplitField(no_excerpt_field=True)
