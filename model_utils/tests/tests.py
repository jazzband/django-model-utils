from __future__ import unicode_literals

from datetime import datetime, timedelta
import pickle
try:
    from unittest import skipUnless
except ImportError: # Python 2.6
    from django.utils.unittest import skipUnless

import django
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.six import text_type
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.test import TestCase

from model_utils import Choices, FieldTracker
from model_utils.fields import get_excerpt, MonitorField, StatusField
from model_utils.managers import QueryManager
from model_utils.models import StatusModel, TimeFramedModel
from model_utils.tests.models import (
    InheritanceManagerTestRelated, InheritanceManagerTestGrandChild1,
    InheritanceManagerTestGrandChild1_2,
    InheritanceManagerTestParent, InheritanceManagerTestChild1,
    InheritanceManagerTestChild2, TimeStamp, Post, Article, Status,
    StatusPlainTuple, TimeFrame, Monitored, StatusManagerAdded,
    TimeFrameManagerAdded, Dude, SplitFieldAbstractParent, Car, Spot,
    ModelTracked, ModelTrackedFK, ModelTrackedNotDefault, ModelTrackedMultiple,
    Tracked, TrackedFK, TrackedNotDefault, TrackedNonFieldAttr,
    TrackedMultiple, StatusFieldDefaultFilled, StatusFieldDefaultNotFilled)



class GetExcerptTests(TestCase):
    def test_split(self):
        e = get_excerpt("some content\n\n<!-- split -->\n\nsome more")
        self.assertEqual(e, 'some content\n')


    def test_auto_split(self):
        e = get_excerpt("para one\n\npara two\n\npara three")
        self.assertEqual(e, 'para one\n\npara two')


    def test_middle_of_para(self):
        e = get_excerpt("some text\n<!-- split -->\nmore text")
        self.assertEqual(e, 'some text')


    def test_middle_of_line(self):
        e = get_excerpt("some text <!-- split --> more text")
        self.assertEqual(e, "some text <!-- split --> more text")



class SplitFieldTests(TestCase):
    full_text = 'summary\n\n<!-- split -->\n\nmore'
    excerpt = 'summary\n'


    def setUp(self):
        self.post = Article.objects.create(
            title='example post', body=self.full_text)


    def test_unicode_content(self):
        self.assertEqual(text_type(self.post.body), self.full_text)


    def test_excerpt(self):
        self.assertEqual(self.post.body.excerpt, self.excerpt)


    def test_content(self):
        self.assertEqual(self.post.body.content, self.full_text)


    def test_has_more(self):
        self.assertTrue(self.post.body.has_more)


    def test_not_has_more(self):
        post = Article.objects.create(title='example 2',
                                      body='some text\n\nsome more\n')
        self.assertFalse(post.body.has_more)


    def test_load_back(self):
        post = Article.objects.get(pk=self.post.pk)
        self.assertEqual(post.body.content, self.post.body.content)
        self.assertEqual(post.body.excerpt, self.post.body.excerpt)


    def test_assign_to_body(self):
        new_text = 'different\n\n<!-- split -->\n\nother'
        self.post.body = new_text
        self.post.save()
        self.assertEqual(text_type(self.post.body), new_text)


    def test_assign_to_content(self):
        new_text = 'different\n\n<!-- split -->\n\nother'
        self.post.body.content = new_text
        self.post.save()
        self.assertEqual(text_type(self.post.body), new_text)


    def test_assign_to_excerpt(self):
        with self.assertRaises(AttributeError):
            self.post.body.excerpt = 'this should fail'


    def test_access_via_class(self):
        with self.assertRaises(AttributeError):
            Article.body


    def test_none(self):
        a = Article(title='Some Title', body=None)
        self.assertEqual(a.body, None)


    def test_assign_splittext(self):
        a = Article(title='Some Title')
        a.body = self.post.body
        self.assertEqual(a.body.excerpt, 'summary\n')


    def test_value_to_string(self):
        f = self.post._meta.get_field('body')
        self.assertEqual(f.value_to_string(self.post), self.full_text)


    def test_abstract_inheritance(self):
        class Child(SplitFieldAbstractParent):
            pass

        self.assertEqual(
            [f.name for f in Child._meta.fields],
            ["id", "content", "_content_excerpt"])



class MonitorFieldTests(TestCase):
    def setUp(self):
        self.instance = Monitored(name='Charlie')
        self.created = self.instance.name_changed


    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


    def test_save_changed(self):
        self.instance.name = 'Maria'
        self.instance.save()
        self.assertTrue(self.instance.name_changed > self.created)


    def test_double_save(self):
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)


    def test_no_monitor_arg(self):
        with self.assertRaises(TypeError):
            MonitorField()


class StatusFieldTests(TestCase):

    def test_status_with_default_filled(self):
        instance = StatusFieldDefaultFilled()
        self.assertEqual(instance.status, instance.STATUS.yes)

    def test_status_with_default_not_filled(self):
        instance = StatusFieldDefaultNotFilled()
        self.assertEqual(instance.status, instance.STATUS.no)

    def test_no_check_for_status(self):
        field = StatusField(no_check_for_status=True)
        # this model has no STATUS attribute, so checking for it would error
        field.prepare_class(Article)

    def test_get_status_display(self):
        instance = StatusFieldDefaultFilled()
        self.assertEqual(instance.get_status_display(), "Yes")


class ChoicesTests(TestCase):
    def setUp(self):
        self.STATUS = Choices('DRAFT', 'PUBLISHED')


    def test_getattr(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')


    def test_indexing(self):
        self.assertEqual(self.STATUS[1], ('PUBLISHED', 'PUBLISHED'))


    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED')))


    def test_len(self):
        self.assertEqual(len(self.STATUS), 2)


    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            ('DRAFT', 'DRAFT', 'DRAFT'),
            ('PUBLISHED', 'PUBLISHED', 'PUBLISHED'),
        )))


    def test_wrong_length_tuple(self):
        with self.assertRaises(ValueError):
            Choices(('a',))

    def test_contains_value(self):
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse('UNPUBLISHED' in self.STATUS)


class LabelChoicesTests(ChoicesTests):
    def setUp(self):
        self.STATUS = Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        )


    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            ('DELETED', 'DELETED'))
        )


    def test_indexing(self):
        self.assertEqual(self.STATUS[1], ('PUBLISHED', 'is published'))


    def test_default(self):
        self.assertEqual(self.STATUS.DELETED, 'DELETED')


    def test_provided(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')


    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)


    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            ('DRAFT', 'DRAFT', 'is draft'),
            ('PUBLISHED', 'PUBLISHED', 'is published'),
            ('DELETED', 'DELETED', 'DELETED'),
        )))

    def test_contains_value(self):
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)
        # This should be True, because both the display value
        # and the internal representation are both DELETED.
        self.assertTrue('DELETED' in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse('UNPUBLISHED' in self.STATUS)

    def test_doesnt_contain_display_value(self):
        self.assertFalse('is draft' in self.STATUS)



class IdentifierChoicesTests(ChoicesTests):
    def setUp(self):
        self.STATUS = Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'))


    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (
                (0, 'is draft'),
                (1, 'is published'),
                (2, 'is deleted')))


    def test_indexing(self):
        self.assertEqual(self.STATUS[1], (1, 'is published'))


    def test_getattr(self):
        self.assertEqual(self.STATUS.DRAFT, 0)


    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)


    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'),
        )))

    def test_contains_value(self):
        self.assertTrue(0 in self.STATUS)
        self.assertTrue(1 in self.STATUS)
        self.assertTrue(2 in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse(3 in self.STATUS)

    def test_doesnt_contain_display_value(self):
        self.assertFalse('is draft' in self.STATUS)

    def test_doesnt_contain_python_attr(self):
        self.assertFalse('PUBLISHED' in self.STATUS)

class InheritanceManagerTests(TestCase):
    def setUp(self):
        self.child1 = InheritanceManagerTestChild1.objects.create()
        self.child2 = InheritanceManagerTestChild2.objects.create()
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create()
        self.grandchild1_2 = \
                InheritanceManagerTestGrandChild1_2.objects.create()


    def get_manager(self):
        return InheritanceManagerTestParent.objects


    def test_normal(self):
        children = set([
                InheritanceManagerTestParent(pk=self.child1.pk),
                InheritanceManagerTestParent(pk=self.child2.pk),
                InheritanceManagerTestParent(pk=self.grandchild1.pk),
                InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
                ])
        self.assertEqual(set(self.get_manager().all()), children)


    def test_select_all_subclasses(self):
        children = set([self.child1, self.child2])
        if django.VERSION >= (1, 6, 0):
            children.add(self.grandchild1)
            children.add(self.grandchild1_2)
        else:
            children.add(InheritanceManagerTestChild1(pk=self.grandchild1.pk))
            children.add(InheritanceManagerTestChild1(pk=self.grandchild1_2.pk))
        self.assertEqual(
            set(self.get_manager().select_subclasses()), children)


    def test_select_specific_subclasses(self):
        children = set([
                self.child1,
                InheritanceManagerTestParent(pk=self.child2.pk),
                InheritanceManagerTestChild1(pk=self.grandchild1.pk),
                InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
                ])
        self.assertEqual(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1")
                ),
            children,
            )


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_select_specific_grandchildren(self):
        children = set([
                InheritanceManagerTestParent(pk=self.child1.pk),
                InheritanceManagerTestParent(pk=self.child2.pk),
                self.grandchild1,
                InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
                ])
        self.assertEqual(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1__"
                    "inheritancemanagertestgrandchild1"
                    )
                ),
            children,
            )


    def test_get_subclass(self):
        self.assertEqual(
            self.get_manager().get_subclass(pk=self.child1.pk),
            self.child1)


    def test_prior_select_related(self):
        with self.assertNumQueries(1):
            obj = self.get_manager().select_related(
                "inheritancemanagertestchild1").select_subclasses(
                "inheritancemanagertestchild2").get(pk=self.child1.pk)
            obj.inheritancemanagertestchild1



class InheritanceManagerRelatedTests(InheritanceManagerTests):
    def setUp(self):
        self.related = InheritanceManagerTestRelated.objects.create()
        self.child1 = InheritanceManagerTestChild1.objects.create(
            related=self.related)
        self.child2 = InheritanceManagerTestChild2.objects.create(
            related=self.related)
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create(related=self.related)
        self.grandchild1_2 = InheritanceManagerTestGrandChild1_2.objects.create(related=self.related)


    def get_manager(self):
        return self.related.imtests


    def test_get_method_with_select_subclasses(self):
        self.assertEqual(
            InheritanceManagerTestParent.objects.select_subclasses().get(
                id=self.child1.id),
            self.child1)


    def test_annotate_with_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.select_subclasses().annotate(
            models.Count('id'))
        self.assertEqual(qs.get(id=self.child1.id).id__count, 1)


    def test_annotate_with_named_arguments_with_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.select_subclasses().annotate(
            test_count=models.Count('id'))
        self.assertEqual(qs.get(id=self.child1.id).test_count, 1)


    def test_annotate_before_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.annotate(
            models.Count('id')).select_subclasses()
        self.assertEqual(qs.get(id=self.child1.id).id__count, 1)


    def test_annotate_with_named_arguments_before_select_subclasses(self):
        qs = InheritanceManagerTestParent.objects.annotate(
            test_count=models.Count('id')).select_subclasses()
        self.assertEqual(qs.get(id=self.child1.id).test_count, 1)



class TimeStampedModelTests(TestCase):
    def test_created(self):
        t1 = TimeStamp.objects.create()
        t2 = TimeStamp.objects.create()
        self.assertTrue(t2.created > t1.created)


    def test_modified(self):
        t1 = TimeStamp.objects.create()
        t2 = TimeStamp.objects.create()
        t1.save()
        self.assertTrue(t2.modified < t1.modified)



class TimeFramedModelTests(TestCase):
    def setUp(self):
        self.now = datetime.now()


    def test_not_yet_begun(self):
        TimeFrame.objects.create(start=self.now+timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 0)


    def test_finished(self):
        TimeFrame.objects.create(end=self.now-timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 0)


    def test_no_end(self):
        TimeFrame.objects.create(start=self.now-timedelta(days=10))
        self.assertEqual(TimeFrame.timeframed.count(), 1)


    def test_no_start(self):
        TimeFrame.objects.create(end=self.now+timedelta(days=2))
        self.assertEqual(TimeFrame.timeframed.count(), 1)


    def test_within_range(self):
        TimeFrame.objects.create(start=self.now-timedelta(days=1),
                                 end=self.now+timedelta(days=1))
        self.assertEqual(TimeFrame.timeframed.count(), 1)



class TimeFrameManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assertTrue(isinstance(TimeFrameManagerAdded.timeframed, QueryManager))


    def test_conflict_error(self):
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(TimeFramedModel):
                timeframed = models.BooleanField()



class StatusModelTests(TestCase):
    def setUp(self):
        self.model = Status
        self.on_hold = Status.STATUS.on_hold
        self.active = Status.STATUS.active


    def test_created(self):
        c1 = self.model.objects.create()
        c2 = self.model.objects.create()
        self.assertTrue(c2.status_changed > c1.status_changed)
        self.assertEqual(self.model.active.count(), 2)
        self.assertEqual(self.model.deleted.count(), 0)


    def test_modification(self):
        t1 = self.model.objects.create()
        date_created = t1.status_changed
        t1.status = self.on_hold
        t1.save()
        self.assertEqual(self.model.active.count(), 0)
        self.assertEqual(self.model.on_hold.count(), 1)
        self.assertTrue(t1.status_changed > date_created)
        date_changed = t1.status_changed
        t1.save()
        self.assertEqual(t1.status_changed, date_changed)
        date_active_again = t1.status_changed
        t1.status = self.active
        t1.save()
        self.assertTrue(t1.status_changed > date_active_again)



class StatusModelPlainTupleTests(StatusModelTests):
    def setUp(self):
        self.model = StatusPlainTuple
        self.on_hold = StatusPlainTuple.STATUS[2][0]
        self.active = StatusPlainTuple.STATUS[0][0]



class StatusManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assertTrue(isinstance(StatusManagerAdded.active, QueryManager))


    def test_conflict_error(self):
        with self.assertRaises(ImproperlyConfigured):
            class ErrorModel(StatusModel):
                STATUS = (
                    ('active', 'active'),
                    ('deleted', 'deleted'),
                    )
                active = models.BooleanField()



class QueryManagerTests(TestCase):
    def setUp(self):
        data = ((True, True, 0),
                (True, False, 4),
                (False, False, 2),
                (False, True, 3),
                (True, True, 1),
                (True, False, 5))
        for p, c, o in data:
            Post.objects.create(published=p, confirmed=c, order=o)


    def test_passing_kwargs(self):
        qs = Post.public.all()
        self.assertEqual([p.order for p in qs], [0, 1, 4, 5])


    def test_passing_Q(self):
        qs = Post.public_confirmed.all()
        self.assertEqual([p.order for p in qs], [0, 1])


    def test_ordering(self):
        qs = Post.public_reversed.all()
        self.assertEqual([p.order for p in qs], [5, 4, 1, 0])



try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = None

@skipUnless(introspector, 'South is not installed')
class SouthFreezingTests(TestCase):
    def test_introspector_adds_no_excerpt_field(self):
        mf = Article._meta.get_field('body')
        args, kwargs = introspector(mf)
        self.assertEqual(kwargs['no_excerpt_field'], 'True')


    def test_no_excerpt_field_works(self):
        from .models import NoRendered
        with self.assertRaises(FieldDoesNotExist):
            NoRendered._meta.get_field('_body_excerpt')

    def test_status_field_no_check_for_status(self):
        sf = StatusFieldDefaultFilled._meta.get_field('status')
        args, kwargs = introspector(sf)
        self.assertEqual(kwargs['no_check_for_status'], 'True')



class PassThroughManagerTests(TestCase):
    def setUp(self):
        Dude.objects.create(name='The Dude', abides=True, has_rug=False)
        Dude.objects.create(name='His Dudeness', abides=False, has_rug=True)
        Dude.objects.create(name='Duder', abides=False, has_rug=False)
        Dude.objects.create(name='El Duderino', abides=True, has_rug=True)


    def test_chaining(self):
        self.assertEqual(Dude.objects.by_name('Duder').count(), 1)
        self.assertEqual(Dude.objects.all().by_name('Duder').count(), 1)
        self.assertEqual(Dude.abiders.rug_positive().count(), 1)
        self.assertEqual(Dude.abiders.all().rug_positive().count(), 1)


    def test_manager_only_methods(self):
        stats = Dude.abiders.get_stats()
        self.assertEqual(stats['rug_count'], 1)
        with self.assertRaises(AttributeError):
            Dude.abiders.all().get_stats()


    def test_queryset_pickling(self):
        qs = Dude.objects.all()
        saltyqs = pickle.dumps(qs)
        unqs = pickle.loads(saltyqs)
        self.assertEqual(unqs.by_name('The Dude').count(), 1)


    def test_queryset_not_available_on_related_manager(self):
        dude = Dude.objects.by_name('Duder').get()
        Car.objects.create(name='Ford', owner=dude)
        self.assertFalse(hasattr(dude.cars_owned, 'by_name'))


class CreatePassThroughManagerTests(TestCase):
    def setUp(self):
        self.dude = Dude.objects.create(name='El Duderino')

    def test_reverse_manager(self):
        Spot.objects.create(
            name='The Crib', owner=self.dude, closed=True, secure=True,
            secret=False)
        self.assertEqual(self.dude.spots_owned.closed().count(), 1)

    def test_related_queryset_pickling(self):
        Spot.objects.create(
            name='The Crib', owner=self.dude, closed=True, secure=True,
            secret=False)
        qs = self.dude.spots_owned.closed()
        pickled_qs = pickle.dumps(qs)
        unpickled_qs = pickle.loads(pickled_qs)
        self.assertEqual(unpickled_qs.secured().count(), 1)

    def test_related_queryset_superclass_method(self):
        Spot.objects.create(
            name='The Crib', owner=self.dude, closed=True, secure=True,
            secret=False)
        Spot.objects.create(
            name='The Secret Crib', owner=self.dude, closed=False, secure=True,
            secret=True)
        self.assertEqual(self.dude.spots_owned.count(), 1)

    def test_related_manager_create(self):
        self.dude.spots_owned.create(name='The Crib', closed=True, secure=True)


class FieldTrackerTestCase(TestCase):

    tracker = None

    def assertHasChanged(self, **kwargs):
        tracker = kwargs.pop('tracker', self.tracker)
        for field, value in kwargs.items():
            if value is None:
                with self.assertRaises(FieldError):
                    tracker.has_changed(field)
            else:
                self.assertEqual(tracker.has_changed(field), value)

    def assertPrevious(self, **kwargs):
        tracker = kwargs.pop('tracker', self.tracker)
        for field, value in kwargs.items():
            self.assertEqual(tracker.previous(field), value)

    def assertChanged(self, **kwargs):
        tracker = kwargs.pop('tracker', self.tracker)
        self.assertEqual(tracker.changed(), kwargs)

    def assertCurrent(self, **kwargs):
        tracker = kwargs.pop('tracker', self.tracker)
        self.assertEqual(tracker.current(), kwargs)

    def update_instance(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self.instance, field, value)
        self.instance.save()


class FieldTrackerCommonTests(object):

    def test_pre_save_previous(self):
        self.assertPrevious(name=None, number=None)
        self.instance.name = 'new age'
        self.instance.number = 8
        self.assertPrevious(name=None, number=None)


class FieldTrackerTests(FieldTrackerTestCase, FieldTrackerCommonTests):

    tracked_class = Tracked

    def setUp(self):
        self.instance = self.tracked_class()
        self.tracker = self.instance.tracker

    def test_descriptor(self):
        self.assertTrue(isinstance(self.tracked_class.tracker, FieldTracker))

    def test_pre_save_changed(self):
        self.assertChanged(name=None)
        self.instance.name = 'new age'
        self.assertChanged(name=None)
        self.instance.number = 8
        self.assertChanged(name=None, number=None)
        self.instance.name = ''
        self.assertChanged(name=None, number=None)

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=False)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=True)

    def test_first_save(self):
        self.assertHasChanged(name=True, number=False)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='', number=None, id=None)
        self.assertChanged(name=None)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertHasChanged(name=True, number=True)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='retro', number=4, id=None)
        self.assertChanged(name=None, number=None)
        # Django 1.4 doesn't have update_fields
        if django.VERSION >= (1, 5, 0):
            self.instance.save(update_fields=[])
            self.assertHasChanged(name=True, number=True)
            self.assertPrevious(name=None, number=None)
            self.assertCurrent(name='retro', number=4, id=None)
            self.assertChanged(name=None, number=None)
            with self.assertRaises(ValueError):
                self.instance.save(update_fields=['number'])

    def test_post_save_has_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertHasChanged(name=False, number=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=False)
        self.instance.number = 8
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'retro'
        self.assertHasChanged(name=False, number=True)

    def test_post_save_previous(self):
        self.update_instance(name='retro', number=4)
        self.instance.name = 'new age'
        self.assertPrevious(name='retro', number=4)

    def test_post_save_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged(name='retro')
        self.instance.number = 8
        self.assertChanged(name='retro', number=4)
        self.instance.name = 'retro'
        self.assertChanged(number=4)

    def test_current(self):
        self.assertCurrent(id=None, name='', number=None)
        self.instance.name = 'new age'
        self.assertCurrent(id=None, name='new age', number=None)
        self.instance.number = 8
        self.assertCurrent(id=None, name='new age', number=8)
        self.instance.save()
        self.assertCurrent(id=self.instance.id, name='new age', number=8)

    @skipUnless(
        django.VERSION >= (1, 5, 0), "Django 1.4 doesn't have update_fields")
    def test_update_fields(self):
        self.update_instance(name='retro', number=4)
        self.assertChanged()
        self.instance.name = 'new age'
        self.instance.number = 8
        self.assertChanged(name='retro', number=4)
        self.instance.save(update_fields=[])
        self.assertChanged(name='retro', number=4)
        self.instance.save(update_fields=['name'])
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertNotEqual(in_db.number, self.instance.number)
        self.assertChanged(number=4)
        self.instance.save(update_fields=['number'])
        self.assertChanged()
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertEqual(in_db.number, self.instance.number)


class FieldTrackedModelCustomTests(FieldTrackerTestCase,
                                   FieldTrackerCommonTests):

    tracked_class = TrackedNotDefault

    def setUp(self):
        self.instance = self.tracked_class()
        self.tracker = self.instance.name_tracker

    def test_pre_save_changed(self):
        self.assertChanged(name=None)
        self.instance.name = 'new age'
        self.assertChanged(name=None)
        self.instance.number = 8
        self.assertChanged(name=None)
        self.instance.name = ''
        self.assertChanged(name=None)

    def test_first_save(self):
        self.assertHasChanged(name=True, number=None)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='')
        self.assertChanged(name=None)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertHasChanged(name=True, number=None)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='retro')
        self.assertChanged(name=None)

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=None)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=None)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=None)

    def test_post_save_has_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertHasChanged(name=False, number=None)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=None)
        self.instance.number = 8
        self.assertHasChanged(name=True, number=None)
        self.instance.name = 'retro'
        self.assertHasChanged(name=False, number=None)

    def test_post_save_previous(self):
        self.update_instance(name='retro', number=4)
        self.instance.name = 'new age'
        self.assertPrevious(name='retro', number=None)

    def test_post_save_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged(name='retro')
        self.instance.number = 8
        self.assertChanged(name='retro')
        self.instance.name = 'retro'
        self.assertChanged()

    def test_current(self):
        self.assertCurrent(name='')
        self.instance.name = 'new age'
        self.assertCurrent(name='new age')
        self.instance.number = 8
        self.assertCurrent(name='new age')
        self.instance.save()
        self.assertCurrent(name='new age')

    @skipUnless(
        django.VERSION >= (1, 5, 0), "Django 1.4 doesn't have update_fields")
    def test_update_fields(self):
        self.update_instance(name='retro', number=4)
        self.assertChanged()
        self.instance.name = 'new age'
        self.instance.number = 8
        self.instance.save(update_fields=['name', 'number'])
        self.assertChanged()


class FieldTrackedModelAttributeTests(FieldTrackerTestCase):

    tracked_class = TrackedNonFieldAttr

    def setUp(self):
        self.instance = self.tracked_class()
        self.tracker = self.instance.tracker

    def test_previous(self):
        self.assertPrevious(rounded=None)
        self.instance.number = 7.5
        self.assertPrevious(rounded=None)
        self.instance.save()
        self.assertPrevious(rounded=8)
        self.instance.number = 7.2
        self.assertPrevious(rounded=8)
        self.instance.save()
        self.assertPrevious(rounded=7)

    def test_has_changed(self):
        self.assertHasChanged(rounded=False)
        self.instance.number = 7.5
        self.assertHasChanged(rounded=True)
        self.instance.save()
        self.assertHasChanged(rounded=False)
        self.instance.number = 7.2
        self.assertHasChanged(rounded=True)
        self.instance.number = 7.8
        self.assertHasChanged(rounded=False)

    def test_changed(self):
        self.assertChanged()
        self.instance.number = 7.5
        self.assertPrevious(rounded=None)
        self.instance.save()
        self.assertPrevious()
        self.instance.number = 7.8
        self.assertPrevious()
        self.instance.number = 7.2
        self.assertPrevious(rounded=8)
        self.instance.save()
        self.assertPrevious()

    def test_current(self):
        self.assertCurrent(rounded=None)
        self.instance.number = 7.5
        self.assertCurrent(rounded=8)
        self.instance.save()
        self.assertCurrent(rounded=8)


class FieldTrackedModelMultiTests(FieldTrackerTestCase,
                                  FieldTrackerCommonTests):

    tracked_class = TrackedMultiple

    def setUp(self):
        self.instance = self.tracked_class()
        self.trackers = [self.instance.name_tracker,
                         self.instance.number_tracker]

    def test_pre_save_changed(self):
        self.tracker = self.instance.name_tracker
        self.assertChanged(name=None)
        self.instance.name = 'new age'
        self.assertChanged(name=None)
        self.instance.number = 8
        self.assertChanged(name=None)
        self.instance.name = ''
        self.assertChanged(name=None)
        self.tracker = self.instance.number_tracker
        self.assertChanged(number=None)
        self.instance.name = 'new age'
        self.assertChanged(number=None)
        self.instance.number = 8
        self.assertChanged(number=None)

    def test_pre_save_has_changed(self):
        self.tracker = self.instance.name_tracker
        self.assertHasChanged(name=True, number=None)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=None)
        self.tracker = self.instance.number_tracker
        self.assertHasChanged(name=None, number=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=None, number=False)

    def test_pre_save_previous(self):
        for tracker in self.trackers:
            self.tracker = tracker
            super(FieldTrackedModelMultiTests, self).test_pre_save_previous()

    def test_post_save_has_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertHasChanged(tracker=self.trackers[0], name=False, number=None)
        self.assertHasChanged(tracker=self.trackers[1], name=None, number=False)
        self.instance.name = 'new age'
        self.assertHasChanged(tracker=self.trackers[0], name=True, number=None)
        self.assertHasChanged(tracker=self.trackers[1], name=None, number=False)
        self.instance.number = 8
        self.assertHasChanged(tracker=self.trackers[0], name=True, number=None)
        self.assertHasChanged(tracker=self.trackers[1], name=None, number=True)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertHasChanged(tracker=self.trackers[0], name=False, number=None)
        self.assertHasChanged(tracker=self.trackers[1], name=None, number=False)

    def test_post_save_previous(self):
        self.update_instance(name='retro', number=4)
        self.instance.name = 'new age'
        self.instance.number = 8
        self.assertPrevious(tracker=self.trackers[0], name='retro', number=None)
        self.assertPrevious(tracker=self.trackers[1], name=None, number=4)

    def test_post_save_changed(self):
        self.update_instance(name='retro', number=4)
        self.assertChanged(tracker=self.trackers[0])
        self.assertChanged(tracker=self.trackers[1])
        self.instance.name = 'new age'
        self.assertChanged(tracker=self.trackers[0], name='retro')
        self.assertChanged(tracker=self.trackers[1])
        self.instance.number = 8
        self.assertChanged(tracker=self.trackers[0], name='retro')
        self.assertChanged(tracker=self.trackers[1], number=4)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertChanged(tracker=self.trackers[0])
        self.assertChanged(tracker=self.trackers[1])

    def test_current(self):
        self.assertCurrent(tracker=self.trackers[0], name='')
        self.assertCurrent(tracker=self.trackers[1], number=None)
        self.instance.name = 'new age'
        self.assertCurrent(tracker=self.trackers[0], name='new age')
        self.assertCurrent(tracker=self.trackers[1], number=None)
        self.instance.number = 8
        self.assertCurrent(tracker=self.trackers[0], name='new age')
        self.assertCurrent(tracker=self.trackers[1], number=8)
        self.instance.save()
        self.assertCurrent(tracker=self.trackers[0], name='new age')
        self.assertCurrent(tracker=self.trackers[1], number=8)


class FieldTrackerForeignKeyTests(FieldTrackerTestCase):

    fk_class = Tracked
    tracked_class = TrackedFK

    def setUp(self):
        self.old_fk = self.fk_class.objects.create(number=8)
        self.instance = self.tracked_class.objects.create(fk=self.old_fk)

    def test_default(self):
        self.tracker = self.instance.tracker
        self.assertChanged()
        self.assertPrevious()
        self.assertCurrent(id=self.instance.id, fk_id=self.old_fk.id)
        self.instance.fk = self.fk_class.objects.create(number=8)
        self.assertChanged(fk_id=self.old_fk.id)
        self.assertPrevious(fk_id=self.old_fk.id)
        self.assertCurrent(id=self.instance.id, fk_id=self.instance.fk_id)

    def test_custom(self):
        self.tracker = self.instance.custom_tracker
        self.assertChanged()
        self.assertPrevious()
        self.assertCurrent(fk_id=self.old_fk.id)
        self.instance.fk = self.fk_class.objects.create(number=8)
        self.assertChanged(fk_id=self.old_fk.id)
        self.assertPrevious(fk_id=self.old_fk.id)
        self.assertCurrent(fk_id=self.instance.fk_id)

    def test_custom_without_id(self):
        with self.assertNumQueries(1):
            self.tracked_class.objects.get()
        self.tracker = self.instance.custom_tracker_without_id
        self.assertChanged()
        self.assertPrevious()
        self.assertCurrent(fk=self.old_fk.id)
        self.instance.fk = self.fk_class.objects.create(number=8)
        self.assertChanged(fk=self.old_fk.id)
        self.assertPrevious(fk=self.old_fk.id)
        self.assertCurrent(fk=self.instance.fk_id)


class ModelTrackerTests(FieldTrackerTests):

    tracked_class = ModelTracked

    def test_pre_save_changed(self):
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()
        self.instance.name = ''
        self.assertChanged()

    def test_first_save(self):
        self.assertHasChanged(name=True, number=True)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='', number=None, id=None)
        self.assertChanged()
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertHasChanged(name=True, number=True)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='retro', number=4, id=None)
        self.assertChanged()
        # Django 1.4 doesn't have update_fields
        if django.VERSION >= (1, 5, 0):
            self.instance.save(update_fields=[])
            self.assertHasChanged(name=True, number=True)
            self.assertPrevious(name=None, number=None)
            self.assertCurrent(name='retro', number=4, id=None)
            self.assertChanged()
            with self.assertRaises(ValueError):
                self.instance.save(update_fields=['number'])

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=True)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=True)


class ModelTrackedModelCustomTests(FieldTrackedModelCustomTests):

    tracked_class = ModelTrackedNotDefault

    def test_first_save(self):
        self.assertHasChanged(name=True, number=True)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='')
        self.assertChanged()
        self.instance.name = 'retro'
        self.instance.number = 4
        self.assertHasChanged(name=True, number=True)
        self.assertPrevious(name=None, number=None)
        self.assertCurrent(name='retro')
        self.assertChanged()

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=True)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=True)

    def test_pre_save_changed(self):
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()
        self.instance.name = ''
        self.assertChanged()


class ModelTrackedModelMultiTests(FieldTrackedModelMultiTests):

    tracked_class = ModelTrackedMultiple

    def test_pre_save_has_changed(self):
        self.tracker = self.instance.name_tracker
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=True)
        self.tracker = self.instance.number_tracker
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=True)

    def test_pre_save_changed(self):
        self.tracker = self.instance.name_tracker
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()
        self.instance.name = ''
        self.assertChanged()
        self.tracker = self.instance.number_tracker
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()


class ModelTrackerForeignKeyTests(FieldTrackerForeignKeyTests):

    fk_class = ModelTracked
    tracked_class = ModelTrackedFK

    def test_custom_without_id(self):
        with self.assertNumQueries(2):
            self.tracked_class.objects.get()
        self.tracker = self.instance.custom_tracker_without_id
        self.assertChanged()
        self.assertPrevious()
        self.assertCurrent(fk=self.old_fk)
        self.instance.fk = self.fk_class.objects.create(number=8)
        self.assertNotEqual(self.instance.fk, self.old_fk)
        self.assertChanged(fk=self.old_fk)
        self.assertPrevious(fk=self.old_fk)
        self.assertCurrent(fk=self.instance.fk)
