from __future__ import unicode_literals

from datetime import datetime, timedelta
try:
    from unittest import skipUnless
except ImportError: # Python 2.6
    from django.utils.unittest import skipUnless

import django
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.six import text_type
from django.core.exceptions import ImproperlyConfigured, FieldError
from django.core.management import call_command
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
    StatusPlainTuple, TimeFrame, Monitored, MonitorWhen, MonitorWhenEmpty, StatusManagerAdded,
    TimeFrameManagerAdded, SplitFieldAbstractParent,
    ModelTracked, ModelTrackedFK, ModelTrackedNotDefault, ModelTrackedMultiple, InheritedModelTracked,
    Tracked, TrackedFK, TrackedNotDefault, TrackedNonFieldAttr, TrackedMultiple,
    InheritedTracked, StatusFieldDefaultFilled, StatusFieldDefaultNotFilled,
    InheritanceManagerTestChild3, StatusFieldChoicesName)


class MigrationsTests(TestCase):
    @skipUnless(django.VERSION >= (1, 7, 0), "test only applies to Django 1.7+")
    def test_makemigrations(self):
        call_command('makemigrations', dry_run=True)


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



class MonitorWhenFieldTests(TestCase):
    """
    Will record changes only when name is 'Jose' or 'Maria'
    """
    def setUp(self):
        self.instance = MonitorWhen(name='Charlie')
        self.created = self.instance.name_changed


    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


    def test_save_changed_to_Jose(self):
        self.instance.name = 'Jose'
        self.instance.save()
        self.assertTrue(self.instance.name_changed > self.created)


    def test_save_changed_to_Maria(self):
        self.instance.name = 'Maria'
        self.instance.save()
        self.assertTrue(self.instance.name_changed > self.created)


    def test_save_changed_to_Pedro(self):
        self.instance.name = 'Pedro'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


    def test_double_save(self):
        self.instance.name = 'Jose'
        self.instance.save()
        changed = self.instance.name_changed
        self.instance.save()
        self.assertEqual(self.instance.name_changed, changed)



class MonitorWhenEmptyFieldTests(TestCase):
    """
    Monitor should never be updated id when is an empty list.
    """
    def setUp(self):
        self.instance = MonitorWhenEmpty(name='Charlie')
        self.created = self.instance.name_changed


    def test_save_no_change(self):
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


    def test_save_changed_to_Jose(self):
        self.instance.name = 'Jose'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)


    def test_save_changed_to_Maria(self):
        self.instance.name = 'Maria'
        self.instance.save()
        self.assertEqual(self.instance.name_changed, self.created)



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

    def test_choices_name(self):
        StatusFieldChoicesName()


class ChoicesTests(TestCase):
    def setUp(self):
        self.STATUS = Choices('DRAFT', 'PUBLISHED')


    def test_getattr(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')


    def test_indexing(self):
        self.assertEqual(self.STATUS['PUBLISHED'], 'PUBLISHED')


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

    def test_deepcopy(self):
        import copy
        self.assertEqual(list(self.STATUS),
                         list(copy.deepcopy(self.STATUS)))


    def test_equality(self):
        self.assertEqual(self.STATUS, Choices('DRAFT', 'PUBLISHED'))


    def test_inequality(self):
        self.assertNotEqual(self.STATUS, ['DRAFT', 'PUBLISHED'])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))


    def test_composability(self):
        self.assertEqual(Choices('DRAFT') + Choices('PUBLISHED'), self.STATUS)
        self.assertEqual(Choices('DRAFT') + ('PUBLISHED',), self.STATUS)
        self.assertEqual(('DRAFT',) + Choices('PUBLISHED'), self.STATUS)


    def test_option_groups(self):
        c = Choices(('group a', ['one', 'two']), ['group b', ('three',)])
        self.assertEqual(
                list(c),
                [
                    ('group a', [('one', 'one'), ('two', 'two')]),
                    ('group b', [('three', 'three')]),
                    ],
                )


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
        self.assertEqual(self.STATUS['PUBLISHED'], 'is published')


    def test_default(self):
        self.assertEqual(self.STATUS.DELETED, 'DELETED')


    def test_provided(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')


    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)


    def test_equality(self):
        self.assertEqual(self.STATUS, Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        ))


    def test_inequality(self):
        self.assertNotEqual(self.STATUS, [
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED'
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))


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


    def test_composability(self):
        self.assertEqual(
            Choices(('DRAFT', 'is draft',)) + Choices(('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )

        self.assertEqual(
            (('DRAFT', 'is draft',),) + Choices(('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )

        self.assertEqual(
            Choices(('DRAFT', 'is draft',)) + (('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )


    def test_option_groups(self):
        c = Choices(
            ('group a', [(1, 'one'), (2, 'two')]),
            ['group b', ((3, 'three'),)]
            )
        self.assertEqual(
                list(c),
                [
                    ('group a', [(1, 'one'), (2, 'two')]),
                    ('group b', [(3, 'three')]),
                    ],
                )



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
        self.assertEqual(self.STATUS[1], 'is published')


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


    def test_equality(self):
        self.assertEqual(self.STATUS, Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ))


    def test_inequality(self):
        self.assertNotEqual(self.STATUS, [
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))


    def test_composability(self):
        self.assertEqual(
            Choices(
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + Choices(
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )

        self.assertEqual(
            Choices(
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + (
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )

        self.assertEqual(
            (
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + Choices(
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )


    def test_option_groups(self):
        c = Choices(
            ('group a', [(1, 'ONE', 'one'), (2, 'TWO', 'two')]),
            ['group b', ((3, 'THREE', 'three'),)]
            )
        self.assertEqual(
                list(c),
                [
                    ('group a', [(1, 'one'), (2, 'two')]),
                    ('group b', [(3, 'three')]),
                    ],
                )


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


    def test_select_subclasses_invalid_relation(self):
        """
        If an invalid relation string is provided, we can provide the user
        with a list which is valid, rather than just have the select_related()
        raise an AttributeError further in.
        """
        regex = '^.+? is not in the discovered subclasses, tried:.+$'
        with self.assertRaisesRegexp(ValueError, regex):
            self.get_manager().select_subclasses('user')


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
                    "inheritancemanagertestchild1__inheritancemanagertestgrandchild1"
                    )
                ),
            children,
            )


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_children_and_grandchildren(self):
        children = set([
                self.child1,
                InheritanceManagerTestParent(pk=self.child2.pk),
                self.grandchild1,
                InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
                ])
        self.assertEqual(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1",
                    "inheritancemanagertestchild1__inheritancemanagertestgrandchild1"
                    )
                ),
            children,
            )


    def test_get_subclass(self):
        self.assertEqual(
            self.get_manager().get_subclass(pk=self.child1.pk),
            self.child1)


    def test_get_subclass_on_queryset(self):
        self.assertEqual(
            self.get_manager().all().get_subclass(pk=self.child1.pk),
            self.child1)


    def test_prior_select_related(self):
        with self.assertNumQueries(1):
            obj = self.get_manager().select_related(
                "inheritancemanagertestchild1").select_subclasses(
                "inheritancemanagertestchild2").get(pk=self.child1.pk)
            obj.inheritancemanagertestchild1


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_version_determining_any_depth(self):
        self.assertIsNone(self.get_manager().all()._get_maximum_depth())


    @skipUnless(django.VERSION < (1, 6, 0), "test only applies to Django < 1.6")
    def test_version_determining_only_child_depth(self):
        self.assertEqual(1, self.get_manager().all()._get_maximum_depth())


    @skipUnless(django.VERSION < (1, 6, 0), "test only applies to Django < 1.6")
    def test_manually_specifying_parent_fk_only_children(self):
        """
        given a Model which inherits from another Model, but also declares
        the OneToOne link manually using `related_name` and `parent_link`,
        ensure that the relation names and subclasses are obtained correctly.
        """
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.all().select_subclasses()

        expected_objs = [self.child1, self.child2,
                         InheritanceManagerTestChild1(pk=self.grandchild1.pk),
                         InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
                         child3]
        self.assertEqual(list(results), expected_objs)

        expected_related_names = [
            'inheritancemanagertestchild1',
            'inheritancemanagertestchild2',
            'manual_onetoone',  # this was set via parent_link & related_name
        ]
        self.assertEqual(set(results.subclasses),
                         set(expected_related_names))


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_manually_specifying_parent_fk_including_grandchildren(self):
        """
        given a Model which inherits from another Model, but also declares
        the OneToOne link manually using `related_name` and `parent_link`,
        ensure that the relation names and subclasses are obtained correctly.
        """
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.all().select_subclasses()

        expected_objs = [self.child1, self.child2, self.grandchild1,
                         self.grandchild1_2, child3]
        self.assertEqual(list(results), expected_objs)

        expected_related_names = [
            'inheritancemanagertestchild1__inheritancemanagertestgrandchild1',
            'inheritancemanagertestchild1__inheritancemanagertestgrandchild1_2',
            'inheritancemanagertestchild1',
            'inheritancemanagertestchild2',
            'manual_onetoone',  # this was set via parent_link & related_name
        ]
        self.assertEqual(set(results.subclasses),
                         set(expected_related_names))


    def test_manually_specifying_parent_fk_single_subclass(self):
        """
        Using a string related_name when the relation is manually defined
        instead of implicit should still work in the same way.
        """
        related_name = 'manual_onetoone'
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.all().select_subclasses(related_name)

        expected_objs = [InheritanceManagerTestParent(pk=self.child1.pk),
                         InheritanceManagerTestParent(pk=self.child2.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
                         child3]
        self.assertEqual(list(results), expected_objs)
        expected_related_names = [related_name]
        self.assertEqual(set(results.subclasses),
                         set(expected_related_names))


    def test_filter_on_values_queryset(self):
        queryset = InheritanceManagerTestChild1.objects.values('id').filter(pk=self.child1.pk)
        self.assertEqual(list(queryset), [{'id': self.child1.pk}])


class InheritanceManagerUsingModelsTests(TestCase):

    def setUp(self):
        self.parent1 = InheritanceManagerTestParent.objects.create()
        self.child1 = InheritanceManagerTestChild1.objects.create()
        self.child2 = InheritanceManagerTestChild2.objects.create()
        self.grandchild1 = InheritanceManagerTestGrandChild1.objects.create()
        self.grandchild1_2 = InheritanceManagerTestGrandChild1_2.objects.create()


    def test_select_subclass_by_child_model(self):
        """
        Confirm that passing a child model works the same as passing the
        select_related manually
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild1").order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestChild1).order_by('pk')
        self.assertEqual(objs.subclasses, objsmodels.subclasses)
        self.assertEqual(list(objs), list(objsmodels))


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_select_subclass_by_grandchild_model(self):
        """
        Confirm that passing a grandchild model works the same as passing the
        select_related manually
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild1__inheritancemanagertestgrandchild1")\
            .order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestGrandChild1).order_by('pk')
        self.assertEqual(objs.subclasses, objsmodels.subclasses)
        self.assertEqual(list(objs), list(objsmodels))


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_selecting_all_subclasses_specifically_grandchildren(self):
        """
        A bare select_subclasses() should achieve the same results as doing
        select_subclasses and specifying all possible subclasses.
        This test checks grandchildren, so only works on 1.6>=
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses().order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestChild1, InheritanceManagerTestChild2,
            InheritanceManagerTestChild3,
            InheritanceManagerTestGrandChild1,
            InheritanceManagerTestGrandChild1_2).order_by('pk')
        self.assertEqual(set(objs.subclasses), set(objsmodels.subclasses))
        self.assertEqual(list(objs), list(objsmodels))


    def test_selecting_all_subclasses_specifically_children(self):
        """
        A bare select_subclasses() should achieve the same results as doing
        select_subclasses and specifying all possible subclasses.

        Note: This is sort of the same test as
        `test_selecting_all_subclasses_specifically_grandchildren` but it
        specifically switches what models are used because that happens
        behind the scenes in a bare select_subclasses(), so we need to
        emulate it.
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses().order_by('pk')

        if django.VERSION >= (1, 6, 0):
            models = (InheritanceManagerTestChild1,
                      InheritanceManagerTestChild2,
                      InheritanceManagerTestChild3,
                      InheritanceManagerTestGrandChild1,
                      InheritanceManagerTestGrandChild1_2)
        else:
            models = (InheritanceManagerTestChild1,
                      InheritanceManagerTestChild2,
                      InheritanceManagerTestChild3)

        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            *models).order_by('pk')
        # order shouldn't matter, I don't think, as long as the resulting
        # queryset (when cast to a list) is the same.
        self.assertEqual(set(objs.subclasses), set(objsmodels.subclasses))
        self.assertEqual(list(objs), list(objsmodels))


    def test_select_subclass_just_self(self):
        """
        Passing in the same model as the manager/queryset is bound against
        (ie: the root parent) should have no effect on the result set.
        """
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestParent).order_by('pk')
        self.assertEqual([], objsmodels.subclasses)
        self.assertEqual(list(objsmodels), [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestParent(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
        ])


    def test_select_subclass_invalid_related_model(self):
        """
        Confirming that giving a stupid model doesn't work.
        """
        regex = '^.+? is not a subclass of .+$'
        with self.assertRaisesRegexp(ValueError, regex):
            InheritanceManagerTestParent.objects.select_subclasses(
                TimeFrame).order_by('pk')



    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_mixing_strings_and_classes_with_grandchildren(self):
        """
        Given arguments consisting of both strings and model classes,
        ensure the right resolutions take place, accounting for the extra
        depth (grandchildren etc) 1.6> allows.
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild2",
            InheritanceManagerTestGrandChild1_2).order_by('pk')
        expecting = ['inheritancemanagertestchild1__inheritancemanagertestgrandchild1_2',
                     'inheritancemanagertestchild2']
        self.assertEqual(set(objs.subclasses), set(expecting))
        expecting2 = [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestChild2(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestGrandChild1_2(pk=self.grandchild1_2.pk),
        ]
        self.assertEqual(list(objs), expecting2)


    def test_mixing_strings_and_classes_with_children(self):
        """
        Given arguments consisting of both strings and model classes,
        ensure the right resolutions take place, walking down as far as
        children.
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild2",
            InheritanceManagerTestChild1).order_by('pk')
        expecting = ['inheritancemanagertestchild1',
                     'inheritancemanagertestchild2']

        self.assertEqual(set(objs.subclasses), set(expecting))
        expecting2 = [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestChild1(pk=self.child1.pk),
            InheritanceManagerTestChild2(pk=self.child2.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
        ]
        self.assertEqual(list(objs), expecting2)


    def test_duplications(self):
        """
        Check that even if the same thing is provided as a string and a model
        that the right results are retrieved.
        """
        # mixing strings and models which evaluate to the same thing is fine.
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild2",
            InheritanceManagerTestChild2).order_by('pk')
        self.assertEqual(list(objs), [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestChild2(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
        ])


    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_child_doesnt_accidentally_get_parent(self):
        """
        Given a Child model which also has an InheritanceManager,
        none of the returned objects should be Parent objects.
        """
        objs = InheritanceManagerTestChild1.objects.select_subclasses(
                InheritanceManagerTestGrandChild1).order_by('pk')
        self.assertEqual([
            InheritanceManagerTestChild1(pk=self.child1.pk),
            InheritanceManagerTestGrandChild1(pk=self.grandchild1.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
        ], list(objs))


    def test_manually_specifying_parent_fk_only_specific_child(self):
        """
        given a Model which inherits from another Model, but also declares
        the OneToOne link manually using `related_name` and `parent_link`,
        ensure that the relation names and subclasses are obtained correctly.
        """
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.all().select_subclasses(
            InheritanceManagerTestChild3)

        expected_objs = [InheritanceManagerTestParent(pk=self.parent1.pk),
                         InheritanceManagerTestParent(pk=self.child1.pk),
                         InheritanceManagerTestParent(pk=self.child2.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1.pk),
                         InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
                         child3]
        self.assertEqual(list(results), expected_objs)

        expected_related_names = ['manual_onetoone']
        self.assertEqual(set(results.subclasses),
                         set(expected_related_names))

    def test_extras_descend(self):
        """
        Ensure that extra(select=) values are copied onto sub-classes.
        """
        results = InheritanceManagerTestParent.objects.select_subclasses().extra(
            select={'foo': 'id + 1'}
        )
        self.assertTrue(all(result.foo == (result.id + 1) for result in results))


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
                    ('active', 'Is Active'),
                    ('deleted', 'Is Deleted'),
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
        self.instance.mutable = [1,2,3]
        self.assertChanged(name=None, number=None, mutable=None)

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=True)
        self.instance.mutable = [1,2,3]
        self.assertHasChanged(name=True, number=True, mutable=True)

    def test_first_save(self):
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='', number=None, id=None, mutable=None)
        self.assertChanged(name=None)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.instance.mutable = [1,2,3]
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1,2,3])
        self.assertChanged(name=None, number=None, mutable=None)
        # Django 1.4 doesn't have update_fields
        if django.VERSION >= (1, 5, 0):
            self.instance.save(update_fields=[])
            self.assertHasChanged(name=True, number=True, mutable=True)
            self.assertPrevious(name=None, number=None, mutable=None)
            self.assertCurrent(name='retro', number=4, id=None, mutable=[1,2,3])
            self.assertChanged(name=None, number=None, mutable=None)
            with self.assertRaises(ValueError):
                self.instance.save(update_fields=['number'])

    def test_post_save_has_changed(self):
        self.update_instance(name='retro', number=4, mutable=[1,2,3])
        self.assertHasChanged(name=False, number=False, mutable=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=False)
        self.instance.number = 8
        self.assertHasChanged(name=True, number=True)
        self.instance.mutable[1] = 4
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.instance.name = 'retro'
        self.assertHasChanged(name=False, number=True, mutable=True)

    def test_post_save_previous(self):
        self.update_instance(name='retro', number=4, mutable=[1,2,3])
        self.instance.name = 'new age'
        self.assertPrevious(name='retro', number=4, mutable=[1,2,3])
        self.instance.mutable[1] = 4
        self.assertPrevious(name='retro', number=4, mutable=[1,2,3])

    def test_post_save_changed(self):
        self.update_instance(name='retro', number=4, mutable=[1,2,3])
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged(name='retro')
        self.instance.number = 8
        self.assertChanged(name='retro', number=4)
        self.instance.name = 'retro'
        self.assertChanged(number=4)
        self.instance.mutable[1] = 4
        self.assertChanged(number=4, mutable=[1,2,3])
        self.instance.mutable = [1,2,3]
        self.assertChanged(number=4)

    def test_current(self):
        self.assertCurrent(id=None, name='', number=None, mutable=None)
        self.instance.name = 'new age'
        self.assertCurrent(id=None, name='new age', number=None, mutable=None)
        self.instance.number = 8
        self.assertCurrent(id=None, name='new age', number=8, mutable=None)
        self.instance.mutable = [1,2,3]
        self.assertCurrent(id=None, name='new age', number=8, mutable=[1,2,3])
        self.instance.mutable[1] = 4
        self.assertCurrent(id=None, name='new age', number=8, mutable=[1,4,3])
        self.instance.save()
        self.assertCurrent(id=self.instance.id, name='new age', number=8, mutable=[1,4,3])

    @skipUnless(
        django.VERSION >= (1, 5, 0), "Django 1.4 doesn't have update_fields")
    def test_update_fields(self):
        self.update_instance(name='retro', number=4, mutable=[1,2,3])
        self.assertChanged()
        self.instance.name = 'new age'
        self.instance.number = 8
        self.instance.mutable = [4,5,6]
        self.assertChanged(name='retro', number=4, mutable=[1,2,3])
        self.instance.save(update_fields=[])
        self.assertChanged(name='retro', number=4, mutable=[1,2,3])
        self.instance.save(update_fields=['name'])
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertNotEqual(in_db.number, self.instance.number)
        self.assertChanged(number=4, mutable=[1,2,3])
        self.instance.save(update_fields=['number'])
        self.assertChanged(mutable=[1,2,3])
        self.instance.save(update_fields=['mutable'])
        self.assertChanged()
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertEqual(in_db.number, self.instance.number)
        self.assertEqual(in_db.mutable, self.instance.mutable)

    def test_with_deferred(self):
        self.instance.name = 'new age'
        self.instance.number = 1
        self.instance.save()
        item = list(self.tracked_class.objects.only('name').all())[0]
        self.assertTrue(item._deferred_fields)

        self.assertEqual(item.tracker.previous('number'), None)
        self.assertTrue('number' in item._deferred_fields)

        self.assertEqual(item.number, 1)
        self.assertTrue('number' not in item._deferred_fields)
        self.assertEqual(item.tracker.previous('number'), 1)
        self.assertFalse(item.tracker.has_changed('number'))

        item.number = 2
        self.assertTrue(item.tracker.has_changed('number'))


class FieldTrackerMultipleInstancesTests(TestCase):

    def test_with_deferred_fields_access_multiple(self):
        Tracked.objects.create(pk=1, name='foo', number=1)
        Tracked.objects.create(pk=2, name='bar', number=2)

        queryset = Tracked.objects.only('id')

        for instance in queryset:
            instance.name


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


class InheritedFieldTrackerTests(FieldTrackerTests):

    tracked_class = InheritedTracked

    def test_child_fields_not_tracked(self):
        self.name2 = 'test'
        self.assertEqual(self.tracker.previous('name2'), None)
        self.assertRaises(FieldError, self.tracker.has_changed, 'name2')


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
        self.instance.mutable = [1,2,3]
        self.assertChanged()

    def test_first_save(self):
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='', number=None, id=None, mutable=None)
        self.assertChanged()
        self.instance.name = 'retro'
        self.instance.number = 4
        self.instance.mutable = [1,2,3]
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1,2,3])
        self.assertChanged()
        # Django 1.4 doesn't have update_fields
        if django.VERSION >= (1, 5, 0):
            self.instance.save(update_fields=[])
            self.assertHasChanged(name=True, number=True, mutable=True)
            self.assertPrevious(name=None, number=None, mutable=None)
            self.assertCurrent(name='retro', number=4, id=None, mutable=[1,2,3])
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


class InheritedModelTrackerTests(ModelTrackerTests):

    tracked_class = InheritedModelTracked

    def test_child_fields_not_tracked(self):
        self.name2 = 'test'
        self.assertEqual(self.tracker.previous('name2'), None)
        self.assertTrue(self.tracker.has_changed('name2'))
