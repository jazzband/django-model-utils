from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel, StatusModel, TimeFramedModel
from model_utils.tracker import ModelTracker
from model_utils.managers import QueryManager, InheritanceManager, PassThroughManager
from model_utils.fields import SplitField, MonitorField, StatusField
from model_utils import Choices



class InheritanceManagerTestRelated(models.Model):
    pass



class InheritanceManagerTestParent(models.Model):
    # FileField is just a handy descriptor-using field. Refs #6.
    non_related_field_using_descriptor = models.FileField(upload_to="test")
    related = models.ForeignKey(
        InheritanceManagerTestRelated, related_name="imtests", null=True)
    normal_field = models.TextField()
    objects = InheritanceManager()



class InheritanceManagerTestChild1(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()
    pass


class InheritanceManagerTestGrandChild1(InheritanceManagerTestChild1):
    text_field = models.TextField()


class InheritanceManagerTestChild2(InheritanceManagerTestParent):
    non_related_field_using_descriptor_2 = models.FileField(upload_to="test")
    normal_field_2 = models.TextField()
    pass



class TimeStamp(TimeStampedModel):
    pass



class TimeFrame(TimeFramedModel):
    pass



class TimeFrameManagerAdded(TimeFramedModel):
    pass



class Monitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name")



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
    published = models.BooleanField()
    confirmed = models.BooleanField()
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
    def get_query_set(self):
        kwargs = {}
        if hasattr(self, "_db"):
            kwargs["using"] = self._db
        return ByAuthorQuerySet(self.model, **kwargs).filter(feature=True)



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
    def get_query_set(self):
        return DudeQuerySet(self.model).abiding()

    def get_stats(self):
        return {
            "abiding_count": self.count(),
            "rug_count": self.rug_positive().count(),
        }



class Dude(models.Model):
    abides = models.BooleanField(default=True)
    name = models.CharField(max_length=20)
    has_rug = models.BooleanField()

    objects = PassThroughManager(DudeQuerySet)
    abiders = AbidingManager()


class Car(models.Model):
    name = models.CharField(max_length=20)
    owner = models.ForeignKey(Dude, related_name='cars_owned')

    objects = PassThroughManager(DudeQuerySet)


class SpotQuerySet(models.query.QuerySet):
    def closed(self):
        return self.filter(closed=True)

    def secured(self):
        return self.filter(secure=True)


class Spot(models.Model):
    name = models.CharField(max_length=20)
    secure = models.BooleanField(default=True)
    closed = models.BooleanField(default=False)
    owner = models.ForeignKey(Dude, related_name='spots_owned')

    objects = PassThroughManager.for_queryset_class(SpotQuerySet)()


class Tracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    tracker = ModelTracker()


class TrackedNotDefault(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])


class TrackedMultiple(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()

    name_tracker = ModelTracker(fields=['name'])
    number_tracker = ModelTracker(fields=['number'])


class StatusFieldDefaultFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField(default=STATUS.yes)


class StatusFieldDefaultNotFilled(models.Model):
    STATUS = Choices((0, "no", "No"), (1, "yes", "Yes"))
    status = StatusField()
