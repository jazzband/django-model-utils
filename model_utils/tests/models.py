from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel, StatusModel, TimeFramedModel
from model_utils.tracker import FieldTracker, ModelTracker
from model_utils.managers import QueryManager, InheritanceManager, PassThroughManager
from model_utils.fields import SplitField, MonitorField, StatusField
from model_utils.tests.fields import MutableField
from model_utils import Choices



class InheritanceManagerTestRelated(models.Model):
    pass



@python_2_unicode_compatible
class InheritanceManagerTestParent(models.Model):
    # FileField is just a handy descriptor-using field. Refs #6.
    non_related_field_using_descriptor = models.FileField(upload_to="test")
    related = models.ForeignKey(
        InheritanceManagerTestRelated, related_name="imtests", null=True)
    normal_field = models.TextField()
    related_self = models.OneToOneField("self", related_name="imtests_self", null=True)
    objects = InheritanceManager()

    def __unicode__(self):
        return unicode(self.pk)

    def __str__(self):
        return "%s(%s)" % (
            self.__class__.__name__[len('InheritanceManagerTest'):],
            self.pk,
            )



class InheritanceManagerTestChild1(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()
    objects = InheritanceManager()



class InheritanceManagerTestGrandChild1(InheritanceManagerTestChild1):
    text_field = models.TextField()



class InheritanceManagerTestGrandChild1_2(InheritanceManagerTestChild1):
    text_field = models.TextField()



class InheritanceManagerTestChild2(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()



class InheritanceManagerTestChild3(InheritanceManagerTestParent):
    parent_ptr = models.OneToOneField(
        InheritanceManagerTestParent, related_name='manual_onetoone',
        parent_link=True)


class TimeStamp(TimeStampedModel):
    pass



class TimeFrame(TimeFramedModel):
    pass



class TimeFrameManagerAdded(TimeFramedModel):
    pass



class Monitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name")



class MonitorWhen(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name", when=["Jose", "Maria"])



class MonitorWhenEmpty(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name", when=[])



class Status(StatusModel):
    STATUS = Choices(
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )



class StatusPlainTuple(StatusModel):
    STATUS = (
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )



class StatusManagerAdded(StatusModel):
    STATUS = (
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )



class Post(models.Model):
    published = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    order = models.IntegerField()

    objects = models.Manager()
    public = QueryManager(published=True)
    public_confirmed = QueryManager(models.Q(published=True) &
                                    models.Q(confirmed=True))
    public_reversed = QueryManager(published=True).order_by("-order")

    class Meta:
        ordering = ("order",)



class Article(models.Model):
    title = models.CharField(max_length=50)
    body = SplitField()



class SplitFieldAbstractParent(models.Model):
    content = SplitField()


    class Meta:
        abstract = True



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
    def get_queryset(self):
        kwargs = {}
        if hasattr(self, "_db"):
            kwargs["using"] = self._db
        return ByAuthorQuerySet(self.model, **kwargs).filter(feature=True)

    get_query_set = get_queryset


class DudeQuerySet(models.query.QuerySet):
    def abiding(self):
        return self.filter(abides=True)

    def rug_positive(self):
        return self.filter(has_rug=True)

    def rug_negative(self):
        return self.filter(has_rug=False)

    def by_name(self, name):
        return self.filter(name__iexact=name)



class AbidingManager(PassThroughManager):
    def get_queryset(self):
        return DudeQuerySet(self.model).abiding()

    get_query_set = get_queryset

    def get_stats(self):
        return {
            "abiding_count": self.count(),
            "rug_count": self.rug_positive().count(),
        }



class Dude(models.Model):
    abides = models.BooleanField(default=True)
    name = models.CharField(max_length=20)
    has_rug = models.BooleanField(default=False)

    objects = PassThroughManager(DudeQuerySet)
    abiders = AbidingManager()


class Car(models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(Dude, related_name='cars_owned')

    objects = PassThroughManager(DudeQuerySet)


class SpotManager(PassThroughManager):
    def get_queryset(self):
        return super(SpotManager, self).get_queryset().filter(secret=False)

    get_query_set = get_queryset


class SpotQuerySet(models.query.QuerySet):
    def closed(self):
        return self.filter(closed=True)

    def secured(self):
        return self.filter(secure=True)


class Spot(models.Model):
    name = models.CharField(max_length=20)
    secure = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    secret = models.BooleanField(default=False)
    owner = models.ForeignKey(Dude, related_name='spots_owned')

    objects = SpotManager.for_queryset_class(SpotQuerySet)()


class Tracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField()

    tracker = FieldTracker()


class TrackedFK(models.Model):
    fk = models.ForeignKey('Tracked')

    tracker = FieldTracker()
    custom_tracker = FieldTracker(fields=['fk_id'])
    custom_tracker_without_id = FieldTracker(fields=['fk'])


class TrackedNotDefault(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = FieldTracker(fields=['name'])


class TrackedNonFieldAttr(models.Model):
    number = models.FloatField()

    @property
    def rounded(self):
        return round(self.number) if self.number is not None else None

    tracker = FieldTracker(fields=['rounded'])


class TrackedMultiple(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = FieldTracker(fields=['name'])
    number_tracker = FieldTracker(fields=['number'])


class InheritedTracked(Tracked):
    name2 = models.CharField(max_length=20)


class ModelTracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField()

    tracker = ModelTracker()


class ModelTrackedFK(models.Model):
    fk = models.ForeignKey('ModelTracked')

    tracker = ModelTracker()
    custom_tracker = ModelTracker(fields=['fk_id'])
    custom_tracker_without_id = ModelTracker(fields=['fk'])


class ModelTrackedNotDefault(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])


class ModelTrackedMultiple(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])
    number_tracker = ModelTracker(fields=['number'])

class InheritedModelTracked(ModelTracked):
    name2 = models.CharField(max_length=20)


class StatusFieldDefaultFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField(default=STATUS.yes)


class StatusFieldDefaultNotFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField()


class StatusFieldChoicesName(models.Model):
    NAMED_STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField(choices_name='NAMED_STATUS')
