from unittest import skipIf

import django
from django.test import TestCase
from django.db.models import Prefetch

from tests.models import InheritanceManagerTestParent, InheritanceManagerTestChild1


class InheritanceIterableTest(TestCase):
    @skipIf(django.VERSION[:2] == (1, 10), "Django 1.10 expects ModelIterable not a subclass of it")
    def test_prefetch(self):
        qs = InheritanceManagerTestChild1.objects.all().prefetch_related(
            Prefetch(
                'normal_field',
                queryset=InheritanceManagerTestParent.objects.all(),
                to_attr='normal_field_prefetched'
            )
        )
        self.assertEqual(qs.count(), 0)
