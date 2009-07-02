from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from model_utils.tests.models import InheritParent, InheritChild

class InheritanceCastModelTests(TestCase):
    def setUp(self):
        self.parent = InheritParent.objects.create()
        self.child = InheritChild.objects.create()
    
    def testParentRealType(self):
        self.assertEquals(self.parent.real_type,
                          ContentType.objects.get_for_model(InheritParent))

    def testChildRealType(self):
        self.assertEquals(self.child.real_type,
                          ContentType.objects.get_for_model(InheritChild))

    def testCast(self):
        obj = InheritParent.objects.get(pk=self.child.pk).cast()
        self.assertEquals(obj.__class__, InheritChild)
