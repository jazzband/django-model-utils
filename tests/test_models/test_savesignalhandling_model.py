from django.db.models.signals import post_save, pre_save
from django.test import TestCase

from tests.models import SaveSignalHandlingTestModel
from tests.signals import post_save_test, pre_save_test


class SaveSignalHandlingModelTests(TestCase):

    def test_pre_save(self):
        pre_save.connect(pre_save_test, sender=SaveSignalHandlingTestModel)

        obj = SaveSignalHandlingTestModel.objects.create(name='Test')
        delattr(obj, 'pre_save_runned')
        obj.name = 'Test A'
        obj.save()
        self.assertEqual(obj.name, 'Test A')
        self.assertTrue(hasattr(obj, 'pre_save_runned'))

        obj = SaveSignalHandlingTestModel.objects.create(name='Test')
        delattr(obj, 'pre_save_runned')
        obj.name = 'Test B'
        obj.save(signals_to_disable=['pre_save'])
        self.assertEqual(obj.name, 'Test B')
        self.assertFalse(hasattr(obj, 'pre_save_runned'))

    def test_post_save(self):
        post_save.connect(post_save_test, sender=SaveSignalHandlingTestModel)

        obj = SaveSignalHandlingTestModel.objects.create(name='Test')
        delattr(obj, 'post_save_runned')
        obj.name = 'Test A'
        obj.save()
        self.assertEqual(obj.name, 'Test A')
        self.assertTrue(hasattr(obj, 'post_save_runned'))

        obj = SaveSignalHandlingTestModel.objects.create(name='Test')
        delattr(obj, 'post_save_runned')
        obj.name = 'Test B'
        obj.save(signals_to_disable=['post_save'])
        self.assertEqual(obj.name, 'Test B')
        self.assertFalse(hasattr(obj, 'post_save_runned'))
