from __future__ import unicode_literals

from django.utils.six import text_type
from django.test import TestCase

from model_utils.tests.models import Article, SplitFieldAbstractParent


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
