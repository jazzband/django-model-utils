from unittest import skip

from django.core.cache import cache
from django.core.exceptions import FieldError
from django.test import TestCase

from model_utils import FieldTracker
from model_utils.tracker import DescriptorWrapper
from tests.models import (
    InheritedModelTracked,
    InheritedTracked,
    InheritedTrackedFK,
    ModelTracked,
    ModelTrackedFK,
    ModelTrackedMultiple,
    ModelTrackedNotDefault,
    Tracked,
    TrackedAbstract,
    TrackedFileField,
    TrackedFK,
    TrackedMultiple,
    TrackedNonFieldAttr,
    TrackedNotDefault,
    TrackerTimeStamped,
)


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


class FieldTrackerCommonTests:

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
        self.instance.mutable = [1, 2, 3]
        self.assertChanged(name=None, number=None, mutable=None)

    def test_pre_save_has_changed(self):
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.instance.name = 'new age'
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.instance.number = 7
        self.assertHasChanged(name=True, number=True)
        self.instance.mutable = [1, 2, 3]
        self.assertHasChanged(name=True, number=True, mutable=True)

    def test_save_with_args(self):
        self.instance.number = 1
        self.instance.save(False, False, None, None)
        self.assertChanged()

    def test_first_save(self):
        self.assertHasChanged(name=True, number=False, mutable=False)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='', number=None, id=None, mutable=None)
        self.assertChanged(name=None)
        self.instance.name = 'retro'
        self.instance.number = 4
        self.instance.mutable = [1, 2, 3]
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1, 2, 3])
        self.assertChanged(name=None, number=None, mutable=None)

        self.instance.save(update_fields=[])
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1, 2, 3])
        self.assertChanged(name=None, number=None, mutable=None)
        with self.assertRaises(ValueError):
            self.instance.save(update_fields=['number'])

    def test_post_save_has_changed(self):
        self.update_instance(name='retro', number=4, mutable=[1, 2, 3])
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
        self.update_instance(name='retro', number=4, mutable=[1, 2, 3])
        self.instance.name = 'new age'
        self.assertPrevious(name='retro', number=4, mutable=[1, 2, 3])
        self.instance.mutable[1] = 4
        self.assertPrevious(name='retro', number=4, mutable=[1, 2, 3])

    def test_post_save_changed(self):
        self.update_instance(name='retro', number=4, mutable=[1, 2, 3])
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged(name='retro')
        self.instance.number = 8
        self.assertChanged(name='retro', number=4)
        self.instance.name = 'retro'
        self.assertChanged(number=4)
        self.instance.mutable[1] = 4
        self.assertChanged(number=4, mutable=[1, 2, 3])
        self.instance.mutable = [1, 2, 3]
        self.assertChanged(number=4)

    def test_current(self):
        self.assertCurrent(id=None, name='', number=None, mutable=None)
        self.instance.name = 'new age'
        self.assertCurrent(id=None, name='new age', number=None, mutable=None)
        self.instance.number = 8
        self.assertCurrent(id=None, name='new age', number=8, mutable=None)
        self.instance.mutable = [1, 2, 3]
        self.assertCurrent(id=None, name='new age', number=8, mutable=[1, 2, 3])
        self.instance.mutable[1] = 4
        self.assertCurrent(id=None, name='new age', number=8, mutable=[1, 4, 3])
        self.instance.save()
        self.assertCurrent(id=self.instance.id, name='new age', number=8, mutable=[1, 4, 3])

    def test_update_fields(self):
        self.update_instance(name='retro', number=4, mutable=[1, 2, 3])
        self.assertChanged()
        self.instance.name = 'new age'
        self.instance.number = 8
        self.instance.mutable = [4, 5, 6]
        self.assertChanged(name='retro', number=4, mutable=[1, 2, 3])
        self.instance.save(update_fields=[])
        self.assertChanged(name='retro', number=4, mutable=[1, 2, 3])
        self.instance.save(update_fields=['name'])
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertNotEqual(in_db.number, self.instance.number)
        self.assertChanged(number=4, mutable=[1, 2, 3])
        self.instance.save(update_fields=['number'])
        self.assertChanged(mutable=[1, 2, 3])
        self.instance.save(update_fields=['mutable'])
        self.assertChanged()
        in_db = self.tracked_class.objects.get(id=self.instance.id)
        self.assertEqual(in_db.name, self.instance.name)
        self.assertEqual(in_db.number, self.instance.number)
        self.assertEqual(in_db.mutable, self.instance.mutable)

    def test_refresh_from_db(self):
        self.update_instance(name='retro', number=4, mutable=[1, 2, 3])
        self.tracked_class.objects.filter(pk=self.instance.pk).update(
            name='new age', number=8, mutable=[3, 2, 1])
        self.assertChanged()
        self.instance.name = 'like in db'
        self.instance.number = 8
        self.instance.mutable = [3, 2, 1]
        self.assertChanged(name='retro', number=4, mutable=[1, 2, 3])
        self.instance.refresh_from_db(fields=('name',))
        self.assertChanged(number=4, mutable=[1, 2, 3])
        self.instance.refresh_from_db(fields={'mutable'})
        self.assertChanged(number=4)
        self.instance.refresh_from_db()
        self.assertChanged()

    def test_with_deferred(self):
        self.instance.name = 'new age'
        self.instance.number = 1
        self.instance.save()
        item = self.tracked_class.objects.only('name').first()
        self.assertTrue(item.get_deferred_fields())

        # has_changed() returns False for deferred fields, without un-deferring them.
        # Use an if because ModelTracked doesn't support has_changed() in this case.
        if self.tracked_class == Tracked:
            self.assertFalse(item.tracker.has_changed('number'))
            self.assertIsInstance(item.__class__.number, DescriptorWrapper)
            self.assertTrue('number' in item.get_deferred_fields())

        # previous() un-defers field and returns value
        self.assertEqual(item.tracker.previous('number'), 1)
        self.assertNotIn('number', item.get_deferred_fields())

        # examining a deferred field un-defers it
        item = self.tracked_class.objects.only('name').first()
        self.assertEqual(item.number, 1)
        self.assertTrue('number' not in item.get_deferred_fields())
        self.assertEqual(item.tracker.previous('number'), 1)
        self.assertFalse(item.tracker.has_changed('number'))

        # has_changed() returns correct values after deferred field is examined
        self.assertFalse(item.tracker.has_changed('number'))
        item.number = 2
        self.assertTrue(item.tracker.has_changed('number'))

        # previous() returns correct value after deferred field is examined
        self.assertEqual(item.tracker.previous('number'), 1)

        # assigning to a deferred field un-defers it
        # Use an if because ModelTracked doesn't handle this case.
        if self.tracked_class == Tracked:

            item = self.tracked_class.objects.only('name').first()
            item.number = 2

            # previous() fetches correct value from database after deferred field is assigned
            self.assertEqual(item.tracker.previous('number'), 1)

            # database fetch of previous() value doesn't affect current value
            self.assertEqual(item.number, 2)

            # has_changed() returns correct values after deferred field is assigned
            self.assertTrue(item.tracker.has_changed('number'))
            item.number = 1
            self.assertFalse(item.tracker.has_changed('number'))


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
            super().test_pre_save_previous()

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


class FieldTrackerTimeStampedTests(FieldTrackerTestCase):

    fk_class = Tracked
    tracked_class = TrackerTimeStamped

    def setUp(self):
        self.instance = self.tracked_class.objects.create(name='old', number=1)
        self.tracker = self.instance.tracker

    def test_set_modified_on_save(self):
        old_modified = self.instance.modified
        self.instance.name = 'new'
        self.instance.save()
        self.assertGreater(self.instance.modified, old_modified)
        self.assertChanged()

    def test_set_modified_on_save_update_fields(self):
        old_modified = self.instance.modified
        self.instance.name = 'new'
        self.instance.save(update_fields=('name',))
        self.assertGreater(self.instance.modified, old_modified)
        self.assertChanged()


class InheritedFieldTrackerTests(FieldTrackerTests):

    tracked_class = InheritedTracked

    def test_child_fields_not_tracked(self):
        self.name2 = 'test'
        self.assertEqual(self.tracker.previous('name2'), None)
        self.assertRaises(FieldError, self.tracker.has_changed, 'name2')


class FieldTrackerInheritedForeignKeyTests(FieldTrackerForeignKeyTests):

    tracked_class = InheritedTrackedFK


class FieldTrackerFileFieldTests(FieldTrackerTestCase):

    tracked_class = TrackedFileField

    def setUp(self):
        self.instance = self.tracked_class()
        self.tracker = self.instance.tracker
        self.some_file = 'something.txt'
        self.another_file = 'another.txt'

    def test_pre_save_changed(self):
        self.assertChanged(some_file=None)
        self.instance.some_file = self.some_file
        self.assertChanged(some_file=None)

    def test_pre_save_has_changed(self):
        self.assertHasChanged(some_file=True)
        self.instance.some_file = self.some_file
        self.assertHasChanged(some_file=True)

    def test_pre_save_previous(self):
        self.assertPrevious(some_file=None)
        self.instance.some_file = self.some_file
        self.assertPrevious(some_file=None)

    def test_post_save_changed(self):
        self.update_instance(some_file=self.some_file)
        self.assertChanged()
        previous_file = self.instance.some_file
        self.instance.some_file = self.another_file
        self.assertChanged(some_file=previous_file)
        # test deferred file field
        deferred_instance = self.tracked_class.objects.defer('some_file')[0]
        deferred_instance.some_file  # access field to fetch from database
        self.assertChanged(tracker=deferred_instance.tracker)

        previous_file = deferred_instance.some_file
        deferred_instance.some_file = self.another_file
        self.assertChanged(
            tracker=deferred_instance.tracker,
            some_file=previous_file,
        )

    def test_post_save_has_changed(self):
        self.update_instance(some_file=self.some_file)
        self.assertHasChanged(some_file=False)
        self.instance.some_file = self.another_file
        self.assertHasChanged(some_file=True)

        # test deferred file field
        deferred_instance = self.tracked_class.objects.defer('some_file')[0]
        deferred_instance.some_file  # access field to fetch from database
        self.assertHasChanged(
            tracker=deferred_instance.tracker,
            some_file=False,
        )

        deferred_instance.some_file = self.another_file
        self.assertHasChanged(
            tracker=deferred_instance.tracker,
            some_file=True,
        )

    def test_post_save_previous(self):
        self.update_instance(some_file=self.some_file)
        previous_file = self.instance.some_file
        self.instance.some_file = self.another_file
        self.assertPrevious(some_file=previous_file)

        # test deferred file field
        deferred_instance = self.tracked_class.objects.defer('some_file')[0]
        deferred_instance.some_file  # access field to fetch from database
        self.assertPrevious(
            tracker=deferred_instance.tracker,
            some_file=previous_file,
        )

        deferred_instance.some_file = self.another_file
        self.assertPrevious(
            tracker=deferred_instance.tracker,
            some_file=previous_file,
        )

    def test_current(self):
        self.assertCurrent(some_file=self.instance.some_file, id=None)
        self.instance.some_file = self.some_file
        self.assertCurrent(some_file=self.instance.some_file, id=None)

        # test deferred file field
        self.instance.save()
        deferred_instance = self.tracked_class.objects.defer('some_file')[0]
        deferred_instance.some_file  # access field to fetch from database
        self.assertCurrent(
            some_file=self.instance.some_file,
            id=self.instance.id,
        )

        self.instance.some_file = self.another_file
        self.assertCurrent(
            some_file=self.instance.some_file,
            id=self.instance.id,
        )


class ModelTrackerTests(FieldTrackerTests):

    tracked_class = ModelTracked

    def test_cache_compatible(self):
        cache.set('key', self.instance)
        instance = cache.get('key')
        instance.number = 1
        instance.name = 'cached'
        instance.save()
        self.assertChanged()
        instance.number = 2
        self.assertHasChanged(number=True)

    def test_pre_save_changed(self):
        self.assertChanged()
        self.instance.name = 'new age'
        self.assertChanged()
        self.instance.number = 8
        self.assertChanged()
        self.instance.name = ''
        self.assertChanged()
        self.instance.mutable = [1, 2, 3]
        self.assertChanged()

    def test_first_save(self):
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='', number=None, id=None, mutable=None)
        self.assertChanged()
        self.instance.name = 'retro'
        self.instance.number = 4
        self.instance.mutable = [1, 2, 3]
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1, 2, 3])
        self.assertChanged()

        self.instance.save(update_fields=[])
        self.assertHasChanged(name=True, number=True, mutable=True)
        self.assertPrevious(name=None, number=None, mutable=None)
        self.assertCurrent(name='retro', number=4, id=None, mutable=[1, 2, 3])
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


@skip
class AbstractModelTrackerTests(ModelTrackerTests):

    tracked_class = TrackedAbstract
