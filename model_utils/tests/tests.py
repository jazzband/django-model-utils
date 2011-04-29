from __future__ import with_statement

import pickle, sys, warnings

from datetime import datetime, timedelta

import django
from django.test import TestCase
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.core.exceptions import ImproperlyConfigured

from django.contrib.contenttypes.models import ContentType

from model_utils import Choices
from model_utils.fields import get_excerpt, MonitorField
from model_utils.managers import QueryManager, manager_from
from model_utils.models import StatusModel, TimeFramedModel
from model_utils.tests.models import (
    InheritParent, InheritChild, InheritChild2, InheritanceManagerTestRelated,
    InheritanceManagerTestParent, InheritanceManagerTestChild1,
    InheritanceManagerTestChild2, TimeStamp, Post, Article, Status,
    StatusPlainTuple, TimeFrame, Monitored, StatusManagerAdded,
    TimeFrameManagerAdded, Entry, Dude, SplitFieldAbstractParent)



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


    def test_repr(self):
        self.assertEquals(repr(self.STATUS),
                          "Choices("
                          "(0, 'DRAFT', 'is draft'), "
                          "(1, 'PUBLISHED', 'is published'), "
                          "(2, 'DELETED', 'is deleted'))")


class InheritanceCastModelTests(TestCase):
    def setUp(self):
        self.parent = InheritParent.objects.create()
        self.child = InheritChild.objects.create()


    def test_parent_real_type(self):
        self.assertEquals(self.parent.real_type,
                          ContentType.objects.get_for_model(InheritParent))


    def test_child_real_type(self):
        self.assertEquals(self.child.real_type,
                          ContentType.objects.get_for_model(InheritChild))


    def test_cast(self):
        obj = InheritParent.objects.get(pk=self.child.pk).cast()
        self.assertEquals(obj.__class__, InheritChild)


    # @@@ Use proper test skipping once Django 1.2 is minimum supported version.
    if sys.version_info >= (2, 6):
        # @@@ catch_warnings only available in Python 2.6 and newer
        def test_pending_deprecation(self):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                InheritParent()
                self.assertEqual(len(w), 1)
                assert issubclass(w[-1].category, PendingDeprecationWarning)



class InheritanceCastQuerysetTests(TestCase):
    def setUp(self):
        self.child = InheritChild.objects.create()
        self.child2 = InheritChild2.objects.create()


    def test_cast_manager(self):
        self.assertEquals(set(InheritParent.objects.cast()),
                          set([self.child, self.child2]))


    def test_cast(self):
        parent = InheritParent.objects.create()
        obj = InheritParent.objects.filter(pk=self.child.pk).cast()[0]
        self.assertEquals(obj.__class__, InheritChild)
        self.assertEquals(set(InheritChild2.objects.all().cast()),
                          set([self.child2]))
        self.assertEquals(set(InheritParent.objects.all().cast()),
                          set([parent, self.child, self.child2]))



# @@@ Use proper test skipping once 1.2 is minimum supported version.
if django.VERSION >= (1, 2):
    class InheritanceManagerTests(TestCase):
        def setUp(self):
            self.child1 = InheritanceManagerTestChild1.objects.create()
            self.child2 = InheritanceManagerTestChild2.objects.create()


        def get_manager(self):
            return InheritanceManagerTestParent.objects


        def test_normal(self):
            self.assertEquals(set(self.get_manager().all()),
                              set([
                        InheritanceManagerTestParent(pk=self.child1.pk),
                        InheritanceManagerTestParent(pk=self.child2.pk),
                        ]))


        def test_select_all_subclasses(self):
            self.assertEquals(
                set(self.get_manager().select_subclasses()),
                set([self.child1, self.child2]))


        def test_select_specific_subclasses(self):
            self.assertEquals(
                set(self.get_manager().select_subclasses(
                        "inheritancemanagertestchild1")),
                set([self.child1,
                     InheritanceManagerTestParent(pk=self.child2.pk)]))


    class InheritanceManagerRelatedTests(InheritanceManagerTests):
        def setUp(self):
            self.related = InheritanceManagerTestRelated.objects.create()
            self.child1 = InheritanceManagerTestChild1.objects.create(
                related=self.related)
            self.child2 = InheritanceManagerTestChild2.objects.create(
                related=self.related)


        def get_manager(self):
            return self.related.imtests



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



# @@@ Use proper test skipping once Django 1.2 is minimum supported version.
try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = None

if introspector is not None:
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



class ManagerFromTests(TestCase):
    def setUp(self):
        Entry.objects.create(author='George', published=True)
        Entry.objects.create(author='George', published=False)
        Entry.objects.create(author='Paul', published=True, feature=True)


    def test_chaining(self):
        self.assertEqual(Entry.objects.by_author('George').published().count(),
                         1)


    def test_function(self):
        self.assertEqual(Entry.objects.unpublished().count(), 1)


    def test_typecheck(self):
        self.assertRaises(TypeError, manager_from, 'somestring')


    def test_custom_get_query_set(self):
        self.assertEqual(Entry.featured.published().count(), 1)


    def test_cant_reconcile_qs_class(self):
        self.assertRaises(TypeError, Entry.broken.all)


    def test_queryset_pickling_fails(self):
        qs = Entry.objects.all()
        def dump_load():
            pqs = pickle.dumps(qs)
            pickle.loads(pqs)
        self.assertRaises(pickle.PicklingError, dump_load)


    # @@@ Use proper test skipping once Django 1.2 is minimum supported version.
    if sys.version_info >= (2, 6):
        # @@@ catch_warnings only available in Python 2.6 and newer
        def test_pending_deprecation(self):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                manager_from()
                self.assertEqual(len(w), 1)
                assert issubclass(w[-1].category, PendingDeprecationWarning)



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
