from datetime import datetime, timedelta

from freezegun import freeze_time

from django.test import TestCase

from tests.models import TimeStamp


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
    
    def test_save_with_update_fields_overrides_modified_provided(self):
        '''
        Tests if the save method updated modified field
        accordingly when update_fields is used as an argument
        and modified is provided
        '''
        with freeze_time(datetime(2020,1,1)):
            t1 = TimeStamp.objects.create()
        
        with freeze_time(datetime(2020,1,2)):
            t1.save(update_fields=['modified'])
        
        self.assertEqual(t1.modified, datetime(2020,1,2))
        
    def test_save_with_update_fields_overrides_modified_not_provided(self):
        '''
        Tests if the save method updated modified field
        accordingly when update_fields is used as an argument
        and modified is not provided
        '''
        with freeze_time(datetime(2020,1,1)):
            t1 = TimeStamp.objects.create()
            
        with freeze_time(datetime(2020,1,2)):
            t1.save(update_fields=[])
            
        self.assertEqual(t1.modified, datetime(2020,1,2))
