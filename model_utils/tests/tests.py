from django.test import TestCase
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import FieldDoesNotExist

from model_utils import ChoiceEnum
from model_utils.fields import get_excerpt
from model_utils.tests.models import InheritParent, InheritChild, TimeStamp, \
    Post, Article


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


class ChoiceEnumTests(TestCase):
    def setUp(self):
        self.STATUS = ChoiceEnum('DRAFT', 'PUBLISHED')

    def test_getattr(self):
        self.assertEquals(self.STATUS.DRAFT, 0)

    def test_getitem(self):
        self.assertEquals(self.STATUS[1], 'PUBLISHED')

    def test_iteration(self):
        self.assertEquals(tuple(self.STATUS), ((0, 'DRAFT'), (1, 'PUBLISHED')))


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

if 'south' in settings.INSTALLED_APPS:
    class SouthFreezingTests(TestCase):
        def test_introspector_adds_no_excerpt_field(self):
            from south.modelsinspector import introspector
            mf = Article._meta.get_field('body')
            args, kwargs = introspector(mf)
            self.assertEquals(kwargs['no_excerpt_field'], 'True')
        
        def test_no_excerpt_field_works(self):
            from models import NoRendered
            self.assertRaises(FieldDoesNotExist,
                              NoRendered._meta.get_field,
                              '_body_excerpt')
