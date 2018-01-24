
from django.db import IntegrityError, transaction
from django.test import TestCase
from tests.models import CIPerson


class CaseInsensitiveFieldTests(TestCase):
    def test_charfield(self):
        CIPerson.objects.create(name='JOE', email='joe@example.com')

        self.assertEqual(CIPerson.objects.filter(name='JOE').count(), 1)
        self.assertEqual(CIPerson.objects.filter(name='Joe').count(), 1)
        self.assertEqual(CIPerson.objects.filter(name='joe').count(), 1)

    def test_emailfield(self):
        CIPerson.objects.create(name='JOE', email='joe@example.com')

        self.assertEqual(CIPerson.objects.filter(email='JOE@example.com').count(), 1)
        self.assertEqual(CIPerson.objects.filter(email='Joe@example.com').count(), 1)
        self.assertEqual(CIPerson.objects.filter(email='joe@example.com').count(), 1)

    def test_unique_constraint(self):
        # email fields are unique
        CIPerson.objects.create(name='Joe', email='joe@example.com')

        with transaction.atomic(), self.assertRaises(IntegrityError):
            CIPerson.objects.create(name='Joe', email='JOE@example.com')

        self.assertEqual(CIPerson.objects.filter(email='JOE@example.com').count(), 1)
