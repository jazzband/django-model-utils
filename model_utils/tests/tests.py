from __future__ import with_statement
import pickle

from datetime import datetime, timedelta

import django
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.test import TestCase

from model_utils import Choices
from model_utils.fields import get_excerpt, MonitorField
from model_utils.managers import QueryManager
from model_utils.models import StatusModel, TimeFramedModel
from model_utils.tests.models import (
    InheritanceManagerTestRelated, InheritanceManagerTestGrandChild1,
    InheritanceManagerTestParent, InheritanceManagerTestChild1,
    InheritanceManagerTestChild2, TimeStamp, Post, Article, Status,
    StatusPlainTuple, TimeFrame, Monitored, StatusManagerAdded,
    TimeFrameManagerAdded, Dude, SplitFieldAbstractParent, Car, Spot,
    Tracked, TrackedNotDefault)



class GetExcerptTests(TestCase):
    def test_split(self):
        e = get_excerpt("some content\n\n<!-- split -->\n\nsome more")
        self.assertEquals(e, 'some content\n')


    def test_auto_split(self):
        e = get_excerpt("para one\n\npara two\n\npara three")
        self.assertEquals(e, 'para one\n\npara two')


    def test_middle_of_para(self):
        e = get_excerpt("some text\n<!-- split -->\nmore text")
        self.assertEquals(e, 'some text')


    def test_middle_of_line(self):
        e = get_excerpt("some text <!-- split --> more text")
        self.assertEquals(e, "some text <!-- split --> more text")



class SplitFieldTests(TestCase):
    full_text = u'summary\n\n<!-- split -->\n\nmore'
    excerpt = u'summary\n'


    def setUp(self):
        self.post = Article.objects.create(
            title='example post', body=self.full_text)


    def test_unicode_content(self):
        self.assertEquals(unicode(self.post.body), self.full_text)


    def test_excerpt(self):
        self.assertEquals(self.post.body.excerpt, self.excerpt)


    def test_content(self):
        self.assertEquals(self.post.body.content, self.full_text)


    def test_has_more(self):
        self.failUnless(self.post.body.has_more)


    def test_not_has_more(self):
        post = Article.objects.create(title='example 2',
                                      body='some text\n\nsome more\n')
        self.failIf(post.body.has_more)


    def test_load_back(self):
        post = Article.objects.get(pk=self.post.pk)
        self.assertEquals(post.body.content, self.post.body.content)
        self.assertEquals(post.body.excerpt, self.post.body.excerpt)


    def test_assign_to_body(self):
        new_text = u'different\n\n<!-- split -->\n\nother'
        self.post.body = new_text
        self.post.save()
        self.assertEquals(unicode(self.post.body), new_text)


    def test_assign_to_content(self):
        new_text = u'different\n\n<!-- split -->\n\nother'
        self.post.body.content = new_text
        self.post.save()
        self.assertEquals(unicode(self.post.body), new_text)


    def test_assign_to_excerpt(self):
        def _invalid_assignment():
            self.post.body.excerpt = 'this should fail'
        self.assertRaises(AttributeError, _invalid_assignment)


    def test_access_via_class(self):
        def _invalid_access():
            Article.body
        self.assertRaises(AttributeError, _invalid_access)


    def test_none(self):
        a = Article(title='Some Title', body=None)
        self.assertEquals(a.body, None)


    def test_assign_splittext(self):
        a = Article(title='Some Title')
        a.body = self.post.body
        self.assertEquals(a.body.excerpt, u'summary\n')


    def test_value_to_string(self):
        f = self.post._meta.get_field('body')
        self.assertEquals(f.value_to_string(self.post), self.full_text)


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
        self.assertEquals(self.instance.name_changed, self.created)


    def test_save_changed(self):
        self.instance.name = 'Maria'
        self.instance.save()
        self.failUnless(self.instance.name_changed > self.created)


    def test_double_save(self):
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEquals(self.instance.name_changed, changed)


    def test_no_monitor_arg(self):
        self.assertRaises(TypeError, MonitorField)



class ChoicesTests(TestCase):
    def setUp(self):
        self.STATUS = Choices('DRAFT', 'PUBLISHED')


    def test_getattr(self):
        self.assertEquals(self.STATUS.DRAFT, 'DRAFT')


    def test_indexing(self):
        self.assertEquals(self.STATUS[1], ('PUBLISHED', 'PUBLISHED'))


    def test_iteration(self):
        self.assertEquals(tuple(self.STATUS), (('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED')))


    def test_len(self):
        self.assertEqual(len(self.STATUS), 2)


    def test_repr(self):
        self.assertEquals(repr(self.STATUS),
                          "Choices("
                          "('DRAFT', 'DRAFT', 'DRAFT'), "
                          "('PUBLISHED', 'PUBLISHED', 'PUBLISHED'))")


    def test_wrong_length_tuple(self):
        self.assertRaises(ValueError, Choices, ('a',))



class LabelChoicesTests(ChoicesTests):
    def setUp(self):
        self.STATUS = Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        )


    def test_iteration(self):
        self.assertEquals(tuple(self.STATUS), (
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            ('DELETED', 'DELETED'))
        )


    def test_indexing(self):
        self.assertEquals(self.STATUS[1], ('PUBLISHED', 'is published'))


    def test_default(self):
        self.assertEquals(self.STATUS.DELETED, 'DELETED')


    def test_provided(self):
        self.assertEquals(self.STATUS.DRAFT, 'DRAFT')


    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)


    def test_repr(self):
        self.assertEquals(repr(self.STATUS),
                          "Choices("
                          "('DRAFT', 'DRAFT', 'is draft'), "
                          "('PUBLISHED', 'PUBLISHED', 'is published'), "
                          "('DELETED', 'DELETED', 'DELETED'))")



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
        self.assertEquals(self.STATUS[1], (1, 'is published'))


    def test_getattr(self):
        self.assertEquals(self.STATUS.DRAFT, 0)


    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)


    def test_repr(self):
        self.assertEquals(repr(self.STATUS),
                          "Choices("
                          "(0, 'DRAFT', 'is draft'), "
                          "(1, 'PUBLISHED', 'is published'), "
                          "(2, 'DELETED', 'is deleted'))")



class InheritanceManagerTests(TestCase):
    def setUp(self):
        self.child1 = InheritanceManagerTestChild1.objects.create()
        self.child2 = InheritanceManagerTestChild2.objects.create()
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create()


    def get_manager(self):
        return InheritanceManagerTestParent.objects


    def test_normal(self):
        children = set([
                InheritanceManagerTestParent(pk=self.child1.pk),
                InheritanceManagerTestParent(pk=self.child2.pk),
                InheritanceManagerTestParent(pk=self.grandchild1.pk),
                ])
        self.assertEquals(set(self.get_manager().all()), children)


    def test_select_all_subclasses(self):
        children = set([self.child1, self.child2])
        if django.VERSION >= (1, 6, 0):
            children.add(self.grandchild1)
        else:
            children.add(InheritanceManagerTestChild1(pk=self.grandchild1.pk))
        self.assertEquals(
            set(self.get_manager().select_subclasses()), children)


    def test_select_specific_subclasses(self):
        children = set([
                self.child1,
                InheritanceManagerTestParent(pk=self.child2.pk),
                InheritanceManagerTestChild1(pk=self.grandchild1.pk),
                ])
        self.assertEquals(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1")
                ),
            children,
            )


    def test_select_specific_grandchildren(self):
        if django.VERSION >= (1, 6, 0):
            children = set([
                    self.child1,
                    InheritanceManagerTestParent(pk=self.child2.pk),
                    self.grandchild1,
                    ])
            self.assertEquals(
                set(
                    self.get_manager().select_subclasses(
                        "inheritancemanagertestchild1__"
                        "inheritancemanagertestgrandchild1"
                        )
                    ),
                children,
                )


    def test_get_subclass(self):
        self.assertEquals(
            self.get_manager().get_subclass(pk=self.child1.pk),
            self.child1)


    def test_prior_select_related(self):
        # Django 1.2 doesn't have assertNumQueries
        if django.VERSION >= (1, 3):
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
        self.assert_(t2.created > t1.created)


    def test_modified(self):
        t1 = TimeStamp.objects.create()
        t2 = TimeStamp.objects.create()
        t1.save()
        self.assert_(t2.modified < t1.modified)



class TimeFramedModelTests(TestCase):
    def setUp(self):
        self.now = datetime.now()


    def test_not_yet_begun(self):
        TimeFrame.objects.create(start=self.now+timedelta(days=2))
        self.assertEquals(TimeFrame.timeframed.count(), 0)


    def test_finished(self):
        TimeFrame.objects.create(end=self.now-timedelta(days=1))
        self.assertEquals(TimeFrame.timeframed.count(), 0)


    def test_no_end(self):
        TimeFrame.objects.create(start=self.now-timedelta(days=10))
        self.assertEquals(TimeFrame.timeframed.count(), 1)


    def test_no_start(self):
        TimeFrame.objects.create(end=self.now+timedelta(days=2))
        self.assertEquals(TimeFrame.timeframed.count(), 1)


    def test_within_range(self):
        TimeFrame.objects.create(start=self.now-timedelta(days=1),
                                 end=self.now+timedelta(days=1))
        self.assertEquals(TimeFrame.timeframed.count(), 1)



class TimeFrameManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assert_(isinstance(TimeFrameManagerAdded.timeframed, QueryManager))


    def test_conflict_error(self):
        def _run():
            class ErrorModel(TimeFramedModel):
                timeframed = models.BooleanField()
        self.assertRaises(ImproperlyConfigured, _run)



class StatusModelTests(TestCase):
    def setUp(self):
        self.model = Status
        self.on_hold = Status.STATUS.on_hold
        self.active = Status.STATUS.active


    def test_created(self):
        c1 = self.model.objects.create()
        c2 = self.model.objects.create()
        self.assert_(c2.status_changed > c1.status_changed)
        self.assertEquals(self.model.active.count(), 2)
        self.assertEquals(self.model.deleted.count(), 0)


    def test_modification(self):
        t1 = self.model.objects.create()
        date_created = t1.status_changed
        t1.status = self.on_hold
        t1.save()
        self.assertEquals(self.model.active.count(), 0)
        self.assertEquals(self.model.on_hold.count(), 1)
        self.assert_(t1.status_changed > date_created)
        date_changed = t1.status_changed
        t1.save()
        self.assertEquals(t1.status_changed, date_changed)
        date_active_again = t1.status_changed
        t1.status = self.active
        t1.save()
        self.assert_(t1.status_changed > date_active_again)



class StatusModelPlainTupleTests(StatusModelTests):
    def setUp(self):
        self.model = StatusPlainTuple
        self.on_hold = StatusPlainTuple.STATUS[2][0]
        self.active = StatusPlainTuple.STATUS[0][0]



class StatusManagerAddedTests(TestCase):
    def test_manager_available(self):
        self.assert_(isinstance(StatusManagerAdded.active, QueryManager))


    def test_conflict_error(self):
        def _run():
            class ErrorModel(StatusModel):
                STATUS = (
                    ('active', 'active'),
                    ('deleted', 'deleted'),
                    )
                active = models.BooleanField()
        self.assertRaises(ImproperlyConfigured, _run)



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
        self.assertEquals([p.order for p in qs], [0, 1, 4, 5])


    def test_passing_Q(self):
        qs = Post.public_confirmed.all()
        self.assertEquals([p.order for p in qs], [0, 1])


    def test_ordering(self):
        qs = Post.public_reversed.all()
        self.assertEquals([p.order for p in qs], [5, 4, 1, 0])



try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = None

# @@@ use skipUnless once Django 1.3 is minimum supported version
if introspector:
    class SouthFreezingTests(TestCase):
        def test_introspector_adds_no_excerpt_field(self):
            mf = Article._meta.get_field('body')
            args, kwargs = introspector(mf)
            self.assertEquals(kwargs['no_excerpt_field'], 'True')


        def test_no_excerpt_field_works(self):
            from models import NoRendered
            self.assertRaises(FieldDoesNotExist,
                              NoRendered._meta.get_field,
                              '_body_excerpt')



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
        def notonqs():
            Dude.abiders.all().get_stats()
        self.assertRaises(AttributeError, notonqs)


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
            name='The Crib', owner=self.dude, closed=True, secure=True)
        self.assertEqual(self.dude.spots_owned.closed().count(), 1)

    def test_related_queryset_pickling(self):
        Spot.objects.create(
            name='The Crib', owner=self.dude, closed=True, secure=True)
        qs = self.dude.spots_owned.closed()
        pickled_qs = pickle.dumps(qs)
        unpickled_qs = pickle.loads(pickled_qs)
        self.assertEqual(unpickled_qs.secured().count(), 1)

    def test_related_manager_create(self):
        self.dude.spots_owned.create(name='The Crib', closed=True, secure=True)


class ModelTrackerTestCase(TestCase):
    def assertHasChanged(self, **kwargs):
        for field, value in kwargs.iteritems():
            if value is None:
                self.assertRaises(FieldError, self.tracker.has_changed, field)
            else:
                self.assertEqual(self.tracker.has_changed(field), value)

    def assertPrevious(self, **kwargs):
        for field, value in kwargs.iteritems():
            self.assertEqual(self.tracker.previous(field), value)

    def assertChanged(self, **kwargs):
        self.assertEqual(self.tracker.changed(), kwargs)

    def assertCurrent(self, **kwargs):
        self.assertEqual(self.tracker.current(), kwargs)

    def update_instance(self, **kwargs):
        for field, value in kwargs.iteritems():
            setattr(self.instance, field, value)
        self.instance.save()


class ModelTrackerCommonTests(object):

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=True)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=True)

    def test_pre_save_changed(self):
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()
        self.instance.name = ''
        self.assertChanged()

    def test_pre_save_previous(self):
        self.assertPrevious(name=None, number=None)
        self.instance.name = 'new age'
        self.instance.number = 8
        self.assertPrevious(name=None, number=None)


class ModelTrackerTests(ModelTrackerTestCase, ModelTrackerCommonTests):
    def setUp(self):
        self.instance = Tracked()
        self.tracker = self.instance.tracker

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


class FieldTrackedModelCustomTests(ModelTrackerTestCase,
                                   ModelTrackerCommonTests):
    def setUp(self):
        self.instance = TrackedNotDefault()
        self.tracker = self.instance.name_tracker

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
