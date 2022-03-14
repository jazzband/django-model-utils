import django
from django.db import models
from django.db.models import Manager
from django.db.models.query_utils import DeferredAttribute
from django.utils.translation import gettext_lazy as _

from model_utils import Choices
from model_utils.fields import MonitorField, SplitField, StatusField, UUIDField
from model_utils.managers import InheritanceManager, JoinManagerMixin, QueryManager
from model_utils.models import (
    SaveSignalHandlingModel,
    SoftDeletableModel,
    StatusModel,
    TimeFramedModel,
    TimeStampedModel,
    UUIDModel,
)
from model_utils.tracker import FieldTracker, ModelTracker
from tests.fields import MutableField
from tests.managers import CustomSoftDeleteManager


class InheritanceManagerTestRelated(models.Model):
    pass


class InheritanceManagerTestParent(models.Model):
    # FileField is just a handy descriptor-using field. Refs #6.
    non_related_field_using_descriptor = models.FileField(upload_to="test")
    related = models.ForeignKey(
        InheritanceManagerTestRelated, related_name="imtests", null=True,
        on_delete=models.CASCADE)
    normal_field = models.TextField()
    related_self = models.OneToOneField(
        "self", related_name="imtests_self", null=True,
        on_delete=models.CASCADE)
    objects = InheritanceManager()

    def __str__(self):
        return "{}({})".format(
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
        parent_link=True, on_delete=models.CASCADE)


class InheritanceManagerTestChild4(InheritanceManagerTestParent):
    other_onetoone = models.OneToOneField(
        InheritanceManagerTestParent, related_name='non_inheritance_relation',
        parent_link=False, on_delete=models.CASCADE)
    # The following is needed because of that Django bug:
    # https://code.djangoproject.com/ticket/29998
    parent_ptr = models.OneToOneField(
        InheritanceManagerTestParent, related_name='child4_onetoone',
        parent_link=True, on_delete=models.CASCADE)


class TimeStamp(TimeStampedModel):
    test_field = models.PositiveSmallIntegerField(default=0)


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


class DoubleMonitored(models.Model):
    name = models.CharField(max_length=25)
    name_changed = MonitorField(monitor="name")
    name2 = models.CharField(max_length=25)
    name_changed2 = MonitorField(monitor="name2")


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


class StatusCustomManager(Manager):
    pass


class AbstractStatusCustomManager(StatusModel):
    STATUS = Choices(
        ("first_choice", _("First choice")),
        ("second_choice", _("Second choice")),
    )

    objects = StatusCustomManager()

    class Meta:
        abstract = True


class StatusCustomManager(AbstractStatusCustomManager):
    title = models.CharField(max_length=50)


class Post(models.Model):
    published = models.BooleanField(default=False)
    confirmed = models.BooleanField(default=False)
    order = models.IntegerField()

    objects = models.Manager()
    public = QueryManager(published=True)
    public_confirmed = QueryManager(
        models.Q(published=True) & models.Q(confirmed=True))
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


class AuthorMixin:
    def by_author(self, name):
        return self.filter(author=name)


class PublishedMixin:
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


class AbstractTracked(models.Model):
    number = 1

    class Meta:
        abstract = True


class Tracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        """ No-op save() to ensure that FieldTracker.patch_save() works. """
        super().save(*args, **kwargs)


class TrackerTimeStamped(TimeStampedModel):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        """ Automatically add "modified" to update_fields."""
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {'modified'}
        super().save(*args, **kwargs)


class TrackedFK(models.Model):
    fk = models.ForeignKey('Tracked', on_delete=models.CASCADE)

    tracker = FieldTracker()
    custom_tracker = FieldTracker(fields=['fk_id'])
    custom_tracker_without_id = FieldTracker(fields=['fk'])


class TrackedAbstract(AbstractTracked):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = FieldTracker()


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


class TrackedFileField(models.Model):
    some_file = models.FileField(upload_to='test_location')

    tracker = FieldTracker()


class InheritedTracked(Tracked):
    name2 = models.CharField(max_length=20)


class InheritedTrackedFK(TrackedFK):
    custom_tracker = FieldTracker(fields=['fk_id'])
    custom_tracker_without_id = FieldTracker(fields=['fk'])


class ModelTracked(models.Model):
    name = models.CharField(max_length=20)
    number = models.IntegerField()
    mutable = MutableField(default=None)

    tracker = ModelTracker()


class ModelTrackedFK(models.Model):
    fk = models.ForeignKey('ModelTracked', on_delete=models.CASCADE)

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


class SoftDeletable(SoftDeletableModel):
    """
    Test model with additional manager for full access to model
    instances.
    """
    name = models.CharField(max_length=20)

    all_objects = models.Manager()


class CustomSoftDelete(SoftDeletableModel):
    is_read = models.BooleanField(default=False)

    objects = CustomSoftDeleteManager()


class StringyDescriptor:
    """
    Descriptor that returns a string version of the underlying integer value.
    """
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        if self.name in obj.get_deferred_fields():
            # This queries the database, and sets the value on the instance.
            if django.VERSION < (3, 0):
                DeferredAttribute(field_name=self.name).__get__(obj, cls)
            else:
                # Since Django 3.0, DeferredAttribute wants a field argument.
                fields_map = {f.name: f for f in cls._meta.fields}
                field = fields_map[self.name]
                DeferredAttribute(field=field).__get__(obj, cls)
        return str(obj.__dict__[self.name])

    def __set__(self, obj, value):
        obj.__dict__[self.name] = int(value)

    def __delete__(self, obj):
        del obj.__dict__[self.name]


class CustomDescriptorField(models.IntegerField):
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, name, StringyDescriptor(name))


class ModelWithCustomDescriptor(models.Model):
    custom_field = CustomDescriptorField()
    tracked_custom_field = CustomDescriptorField()
    regular_field = models.IntegerField()
    tracked_regular_field = models.IntegerField()

    tracker = FieldTracker(fields=['tracked_custom_field', 'tracked_regular_field'])


class JoinManager(JoinManagerMixin, models.Manager):
    pass


class BoxJoinModel(models.Model):
    name = models.CharField(max_length=32)
    objects = JoinManager()


class JoinItemForeignKey(models.Model):
    weight = models.IntegerField()
    belonging = models.ForeignKey(
        BoxJoinModel,
        null=True,
        on_delete=models.CASCADE
    )
    objects = JoinManager()


class CustomUUIDModel(UUIDModel):
    pass


class CustomNotPrimaryUUIDModel(models.Model):
    uuid = UUIDField(primary_key=False)


class SaveSignalHandlingTestModel(SaveSignalHandlingModel):
    name = models.CharField(max_length=20)


class TimeStampWithStatusModel(TimeStampedModel, StatusModel):
    STATUS = Choices(
        ("active", _("active")),
        ("deleted", _("deleted")),
        ("on_hold", _("on hold")),
    )

    test_field = models.PositiveSmallIntegerField(default=0)
