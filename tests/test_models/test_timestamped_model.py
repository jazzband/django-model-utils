from datetime import datetime, timedelta

from django.test import TestCase
from freezegun import freeze_time

from tests.models import TimeStamp, TimeStampWithStatusModel


class TimeStampedModelTests(TestCase):
    def test_created(self):
        with freeze_time(datetime(2016, 1, 1)):
            t1 = TimeStamp.objects.create()
        self.assertEqual(t1.created, datetime(2016, 1, 1))

    def test_created_sets_modified(self):
        '''
        Ensure that on creation that modifed is set exactly equal to created.
        '''
        t1 = TimeStamp.objects.create()
        self.assertEqual(t1.created, t1.modified)

    def test_modified(self):
        with freeze_time(datetime(2016, 1, 1)):
            t1 = TimeStamp.objects.create()

        with freeze_time(datetime(2016, 1, 2)):
            t1.save()

        self.assertEqual(t1.modified, datetime(2016, 1, 2))

    def test_overriding_created_via_object_creation_also_uses_creation_date_for_modified(self):
        """
        Setting the created date when first creating an object
        should be permissable.
        """
        different_date = datetime.today() - timedelta(weeks=52)
        t1 = TimeStamp.objects.create(created=different_date)
        self.assertEqual(t1.created, different_date)
        self.assertEqual(t1.modified, different_date)

    def test_overriding_modified_via_object_creation(self):
        """
        Setting the modified date explicitly should be possible when
        first creating an object, but not thereafter.
        """
        different_date = datetime.today() - timedelta(weeks=52)
        t1 = TimeStamp.objects.create(modified=different_date)
        self.assertEqual(t1.modified, different_date)
        self.assertNotEqual(t1.created, different_date)

    def test_overriding_created_after_object_created(self):
        """
        The created date may be changed post-create
        """
        t1 = TimeStamp.objects.create()
        different_date = datetime.today() - timedelta(weeks=52)
        t1.created = different_date
        t1.save()
        self.assertEqual(t1.created, different_date)

    def test_overriding_modified_after_object_created(self):
        """
        The modified date should always be updated when the object
        is saved, regardless of attempts to change it.
        """
        t1 = TimeStamp.objects.create()
        different_date = datetime.today() - timedelta(weeks=52)
        t1.modified = different_date
        t1.save()
        self.assertNotEqual(t1.modified, different_date)

    def test_overrides_using_save(self):
        """
        The first time an object is saved, allow modification of both
        created and modified fields.
        After that, only created may be modified manually.
        """
        t1 = TimeStamp()
        different_date = datetime.today() - timedelta(weeks=52)
        t1.created = different_date
        t1.modified = different_date
        t1.save()
        self.assertEqual(t1.created, different_date)
        self.assertEqual(t1.modified, different_date)
        different_date2 = datetime.today() - timedelta(weeks=26)
        t1.created = different_date2
        t1.modified = different_date2
        t1.save()
        self.assertEqual(t1.created, different_date2)
        self.assertNotEqual(t1.modified, different_date2)
        self.assertNotEqual(t1.modified, different_date)

    def test_save_with_update_fields_overrides_modified_provided_within_a(self):
        """
        Tests if the save method updated modified field
        accordingly when update_fields is used as an argument
        and modified is provided
        """
        tests = (
            ['modified'],  # list
            ('modified',),  # tuple
            {'modified'},  # set
        )

        for update_fields in tests:
            with self.subTest(update_fields=update_fields):
                with freeze_time(datetime(2020, 1, 1)):
                    t1 = TimeStamp.objects.create()

                with freeze_time(datetime(2020, 1, 2)):
                    t1.save(update_fields=update_fields)
                self.assertEqual(t1.modified, datetime(2020, 1, 2))

    def test_save_is_skipped_for_empty_update_fields_iterable(self):
        tests = (
            [],  # list
            (),  # tuple
            set(),  # set
        )

        for update_fields in tests:
            with self.subTest(update_fields=update_fields):
                with freeze_time(datetime(2020, 1, 1)):
                    t1 = TimeStamp.objects.create()

                with freeze_time(datetime(2020, 1, 2)):
                    t1.test_field = 1
                    t1.save(update_fields=update_fields)

                t1.refresh_from_db()
                self.assertEqual(t1.test_field, 0)
                self.assertEqual(t1.modified, datetime(2020, 1, 1))

    def test_save_updates_modified_value_when_update_fields_explicitly_set_to_none(self):
        with freeze_time(datetime(2020, 1, 1)):
            t1 = TimeStamp.objects.create()

        with freeze_time(datetime(2020, 1, 2)):
            t1.save(update_fields=None)

        self.assertEqual(t1.modified, datetime(2020, 1, 2))

    def test_model_inherit_timestampmodel_and_statusmodel(self):
        with freeze_time(datetime(2020, 1, 1)):
            t1 = TimeStampWithStatusModel.objects.create()

        with freeze_time(datetime(2020, 1, 2)):
            t1.save(update_fields=['test_field', 'status'])

        self.assertEqual(t1.modified, datetime(2020, 1, 2))
