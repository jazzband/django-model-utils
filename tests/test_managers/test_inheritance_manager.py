from django.db import models
from django.test import TestCase

from tests.models import (
    InheritanceManagerTestChild1,
    InheritanceManagerTestChild2,
    InheritanceManagerTestChild3,
    InheritanceManagerTestChild4,
    InheritanceManagerTestGrandChild1,
    InheritanceManagerTestGrandChild1_2,
    InheritanceManagerTestParent,
    InheritanceManagerTestRelated,
    TimeFrame,
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
        children = {
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestParent(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
        }
        self.assertEqual(set(self.get_manager().all()), children)

    def test_select_all_subclasses(self):
        children = {self.child1, self.child2}
        children.add(self.grandchild1)
        children.add(self.grandchild1_2)
        self.assertEqual(
            set(self.get_manager().select_subclasses()), children)

    def test_select_subclasses_invalid_relation(self):
        """
        If an invalid relation string is provided, we can provide the user
        with a list which is valid, rather than just have the select_related()
        raise an AttributeError further in.
        """
        regex = '^.+? is not in the discovered subclasses, tried:.+$'
        with self.assertRaisesRegex(ValueError, regex):
            self.get_manager().select_subclasses('user')

    def test_select_specific_subclasses(self):
        children = {
            self.child1,
            InheritanceManagerTestParent(pk=self.child2.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1.pk),
            InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
        }
        self.assertEqual(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1")
            ),
            children,
        )

    def test_select_specific_grandchildren(self):
        children = {
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestParent(pk=self.child2.pk),
            self.grandchild1,
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
        }
        self.assertEqual(
            set(
                self.get_manager().select_subclasses(
                    "inheritancemanagertestchild1__inheritancemanagertestgrandchild1"
                )
            ),
            children,
        )

    def test_children_and_grandchildren(self):
        children = {
            self.child1,
            InheritanceManagerTestParent(pk=self.child2.pk),
            self.grandchild1,
            InheritanceManagerTestChild1(pk=self.grandchild1_2.pk),
        }
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

    def test_manually_specifying_parent_fk_including_grandchildren(self):
        """
        given a Model which inherits from another Model, but also declares
        the OneToOne link manually using `related_name` and `parent_link`,
        ensure that the relation names and subclasses are obtained correctly.
        """
        child3 = InheritanceManagerTestChild3.objects.create()
        qs = InheritanceManagerTestParent.objects.all()
        results = qs.select_subclasses().order_by('pk')

        expected_objs = [
            self.child1,
            self.child2,
            self.grandchild1,
            self.grandchild1_2,
            child3
        ]
        self.assertEqual(list(results), expected_objs)

        expected_related_names = [
            'inheritancemanagertestchild1__inheritancemanagertestgrandchild1',
            'inheritancemanagertestchild1__inheritancemanagertestgrandchild1_2',
            'inheritancemanagertestchild1',
            'inheritancemanagertestchild2',
            'manual_onetoone',  # this was set via parent_link & related_name
            'child4_onetoone',
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
        qs = InheritanceManagerTestParent.objects.all()
        results = qs.select_subclasses(related_name).order_by('pk')

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

    def test_values_list_on_select_subclasses(self):
        """
        Using `select_subclasses` in conjunction with `values_list()` raised an
        exception in `_get_sub_obj_recurse()` because the result of `values_list()`
        is either a `tuple` or primitive objects if `flat=True` is specified,
        because no type checking was done prior to fetching child nodes.
        """

        # Querysets are cast to lists to force immediate evaluation.
        # No exceptions must be thrown.

        # No argument to select_subclasses
        objs_1 = list(
            self.get_manager()
                .select_subclasses()
                .values_list('id')
        )

        # String argument to select_subclasses
        objs_2 = list(
            self.get_manager()
            .select_subclasses(
                "inheritancemanagertestchild2"
            )
            .values_list('id')
        )

        # String argument to select_subclasses
        objs_3 = list(
            self.get_manager()
            .select_subclasses(
                InheritanceManagerTestChild2
            ).values_list('id')
        )

        assert all((
            isinstance(objs_1, list),
            isinstance(objs_2, list),
            isinstance(objs_3, list),
        ))

        assert objs_1 == objs_2 == objs_3


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

    def test_select_subclass_by_grandchild_model(self):
        """
        Confirm that passing a grandchild model works the same as passing the
        select_related manually
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses(
            "inheritancemanagertestchild1__inheritancemanagertestgrandchild1") \
            .order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestGrandChild1).order_by('pk')
        self.assertEqual(objs.subclasses, objsmodels.subclasses)
        self.assertEqual(list(objs), list(objsmodels))

    def test_selecting_all_subclasses_specifically_grandchildren(self):
        """
        A bare select_subclasses() should achieve the same results as doing
        select_subclasses and specifying all possible subclasses.
        This test checks grandchildren, so only works on 1.6>=
        """
        objs = InheritanceManagerTestParent.objects.select_subclasses().order_by('pk')
        objsmodels = InheritanceManagerTestParent.objects.select_subclasses(
            InheritanceManagerTestChild1, InheritanceManagerTestChild2,
            InheritanceManagerTestChild3, InheritanceManagerTestChild4,
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

        models = (InheritanceManagerTestChild1,
                  InheritanceManagerTestChild2,
                  InheritanceManagerTestChild3,
                  InheritanceManagerTestChild4,
                  InheritanceManagerTestGrandChild1,
                  InheritanceManagerTestGrandChild1_2)

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
        with self.assertRaisesRegex(ValueError, regex):
            InheritanceManagerTestParent.objects.select_subclasses(
                TimeFrame).order_by('pk')

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
            InheritanceManagerTestChild3).order_by('pk')

        expected_objs = [
            InheritanceManagerTestParent(pk=self.parent1.pk),
            InheritanceManagerTestParent(pk=self.child1.pk),
            InheritanceManagerTestParent(pk=self.child2.pk),
            InheritanceManagerTestParent(pk=self.grandchild1.pk),
            InheritanceManagerTestParent(pk=self.grandchild1_2.pk),
            child3
        ]
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

    def test_limit_to_specific_subclass(self):
        child3 = InheritanceManagerTestChild3.objects.create()
        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestChild3)

        self.assertEqual([child3], list(results))

    def test_limit_to_specific_grandchild_class(self):
        grandchild1 = InheritanceManagerTestGrandChild1.objects.get()
        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestGrandChild1)

        self.assertEqual([grandchild1], list(results))

    def test_limit_to_child_fetches_grandchildren_as_child_class(self):
        # Not sure if this is the desired behaviour...?
        children = InheritanceManagerTestChild1.objects.all()

        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestChild1)

        self.assertEqual(set(children), set(results))

    def test_can_fetch_limited_class_grandchildren(self):
        # Not sure if this is the desired behaviour...?
        children = InheritanceManagerTestChild1.objects.select_subclasses()

        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestChild1).select_subclasses()

        self.assertEqual(set(children), set(results))

    def test_selecting_multiple_instance_classes(self):
        child3 = InheritanceManagerTestChild3.objects.create()
        children1 = InheritanceManagerTestChild1.objects.all()

        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestChild3, InheritanceManagerTestChild1)

        self.assertEqual(set([child3] + list(children1)), set(results))

    def test_selecting_multiple_instance_classes_including_grandchildren(self):
        child3 = InheritanceManagerTestChild3.objects.create()
        grandchild1 = InheritanceManagerTestGrandChild1.objects.get()

        results = InheritanceManagerTestParent.objects.instance_of(InheritanceManagerTestChild3, InheritanceManagerTestGrandChild1).select_subclasses()

        self.assertEqual({child3, grandchild1}, set(results))

    def test_select_subclasses_interaction_with_instance_of(self):
        child3 = InheritanceManagerTestChild3.objects.create()

        results = InheritanceManagerTestParent.objects.select_subclasses(InheritanceManagerTestChild1).instance_of(InheritanceManagerTestChild3)

        self.assertEqual({child3}, set(results))


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

    def test_get_method_with_select_subclasses_check_for_useless_join(self):
        child4 = InheritanceManagerTestChild4.objects.create(related=self.related, other_onetoone=self.child1)
        self.assertEqual(
            str(InheritanceManagerTestChild4.objects.select_subclasses().filter(
                id=child4.id).query),
            str(InheritanceManagerTestChild4.objects.select_subclasses().select_related(None).filter(
                id=child4.id).query))

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

    def test_clone_when_inheritance_queryset_selects_subclasses_should_clone_them_too(self):
        qs = InheritanceManagerTestParent.objects.select_subclasses()
        self.assertEqual(qs.subclasses, qs._clone().subclasses)
