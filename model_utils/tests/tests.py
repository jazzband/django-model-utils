from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from model_utils.tests.models import InheritParent, InheritChild, TimeStamp, \
    Post

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


class TimeStampedModelTests(TestCase):
    def testCreated(self):
        t1 = TimeStamp.objects.create()
        t2 = TimeStamp.objects.create()
        self.assert_(t2.created > t1.created)

    def testModified(self):
        t1 = TimeStamp.objects.create()
        t2 = TimeStamp.objects.create()
        t1.save()
        self.assert_(t2.modified < t1.modified)

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

    def testPassingKwargs(self):
        qs = Post.public.all()
        self.assertEquals([p.order for p in qs], [0, 1, 4, 5])

    def testPassingQ(self):
        qs = Post.public_confirmed.all()
        self.assertEquals([p.order for p in qs], [0, 1])

    def testOrdering(self):
        qs = Post.public_reversed.all()
        self.assertEquals([p.order for p in qs], [5, 4, 1, 0])
