from django.db.models import Prefetch
from django.test import TestCase

from tests.models import InheritanceManagerTestChild1, InheritanceManagerTestParent


class InheritanceIterableTest(TestCase):
    def test_prefetch(self):
        qs = InheritanceManagerTestChild1.objects.all().prefetch_related(
            Prefetch(
                'normal_field',
                queryset=InheritanceManagerTestParent.objects.all(),
                to_attr='normal_field_prefetched'
            )
        )
        self.assertEqual(qs.count(), 0)
