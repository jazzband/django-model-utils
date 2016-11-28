from __future__ import unicode_literals

from django.test import TestCase

from model_utils.tests.models import Post


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

    def test_passing_kwargs(self):
        qs = Post.public.all()
        self.assertEqual([p.order for p in qs], [0, 1, 4, 5])

    def test_passing_Q(self):
        qs = Post.public_confirmed.all()
        self.assertEqual([p.order for p in qs], [0, 1])

    def test_ordering(self):
        qs = Post.public_reversed.all()
        self.assertEqual([p.order for p in qs], [5, 4, 1, 0])
