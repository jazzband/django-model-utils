from __future__ import unicode_literals

import django

from model_utils.tests.models import (
    ModelTracked, ModelTrackedFK, ModelTrackedNotDefault, ModelTrackedMultiple, InheritedModelTracked,
)

from model_utils.tests.test_fields.test_field_tracker import (
    FieldTrackerTests, FieldTrackedModelCustomTests,
    FieldTrackedModelMultiTests, FieldTrackerForeignKeyTests
)


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
