from __future__ import unicode_literals

from django.test import TestCase

from model_utils import Choices


class ChoicesTests(TestCase):
    def setUp(self):
        self.STATUS = Choices('DRAFT', 'PUBLISHED')

    def test_getattr(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')

    def test_indexing(self):
        self.assertEqual(self.STATUS['PUBLISHED'], 'PUBLISHED')

    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED')))

    def test_len(self):
        self.assertEqual(len(self.STATUS), 2)

    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            ('DRAFT', 'DRAFT', 'DRAFT'),
            ('PUBLISHED', 'PUBLISHED', 'PUBLISHED'),
        )))

    def test_wrong_length_tuple(self):
        with self.assertRaises(ValueError):
            Choices(('a',))

    def test_contains_value(self):
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse('UNPUBLISHED' in self.STATUS)

    def test_deepcopy(self):
        import copy
        self.assertEqual(list(self.STATUS),
                         list(copy.deepcopy(self.STATUS)))

    def test_equality(self):
        self.assertEqual(self.STATUS, Choices('DRAFT', 'PUBLISHED'))

    def test_inequality(self):
        self.assertNotEqual(self.STATUS, ['DRAFT', 'PUBLISHED'])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))

    def test_composability(self):
        self.assertEqual(Choices('DRAFT') + Choices('PUBLISHED'), self.STATUS)
        self.assertEqual(Choices('DRAFT') + ('PUBLISHED',), self.STATUS)
        self.assertEqual(('DRAFT',) + Choices('PUBLISHED'), self.STATUS)

    def test_option_groups(self):
        c = Choices(('group a', ['one', 'two']), ['group b', ('three',)])
        self.assertEqual(
            list(c),
            [
                ('group a', [('one', 'one'), ('two', 'two')]),
                ('group b', [('three', 'three')]),
            ],
        )


class LabelChoicesTests(ChoicesTests):
    def setUp(self):
        self.STATUS = Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        )

    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            ('DELETED', 'DELETED'))
                         )

    def test_indexing(self):
        self.assertEqual(self.STATUS['PUBLISHED'], 'is published')

    def test_default(self):
        self.assertEqual(self.STATUS.DELETED, 'DELETED')

    def test_provided(self):
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')

    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)

    def test_equality(self):
        self.assertEqual(self.STATUS, Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        ))

    def test_inequality(self):
        self.assertNotEqual(self.STATUS, [
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED'
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))

    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            ('DRAFT', 'DRAFT', 'is draft'),
            ('PUBLISHED', 'PUBLISHED', 'is published'),
            ('DELETED', 'DELETED', 'DELETED'),
        )))

    def test_contains_value(self):
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)
        # This should be True, because both the display value
        # and the internal representation are both DELETED.
        self.assertTrue('DELETED' in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse('UNPUBLISHED' in self.STATUS)

    def test_doesnt_contain_display_value(self):
        self.assertFalse('is draft' in self.STATUS)

    def test_composability(self):
        self.assertEqual(
            Choices(('DRAFT', 'is draft',)) + Choices(('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )

        self.assertEqual(
            (('DRAFT', 'is draft',),) + Choices(('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )

        self.assertEqual(
            Choices(('DRAFT', 'is draft',)) + (('PUBLISHED', 'is published'), 'DELETED'),
            self.STATUS
        )

    def test_option_groups(self):
        c = Choices(
            ('group a', [(1, 'one'), (2, 'two')]),
            ['group b', ((3, 'three'),)]
        )
        self.assertEqual(
            list(c),
            [
                ('group a', [(1, 'one'), (2, 'two')]),
                ('group b', [(3, 'three')]),
            ],
        )


class IdentifierChoicesTests(ChoicesTests):
    def setUp(self):
        self.STATUS = Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'))

    def test_iteration(self):
        self.assertEqual(tuple(self.STATUS), (
            (0, 'is draft'),
            (1, 'is published'),
            (2, 'is deleted')))

    def test_indexing(self):
        self.assertEqual(self.STATUS[1], 'is published')

    def test_getattr(self):
        self.assertEqual(self.STATUS.DRAFT, 0)

    def test_len(self):
        self.assertEqual(len(self.STATUS), 3)

    def test_repr(self):
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'),
        )))

    def test_contains_value(self):
        self.assertTrue(0 in self.STATUS)
        self.assertTrue(1 in self.STATUS)
        self.assertTrue(2 in self.STATUS)

    def test_doesnt_contain_value(self):
        self.assertFalse(3 in self.STATUS)

    def test_doesnt_contain_display_value(self):
        self.assertFalse('is draft' in self.STATUS)

    def test_doesnt_contain_python_attr(self):
        self.assertFalse('PUBLISHED' in self.STATUS)

    def test_equality(self):
        self.assertEqual(self.STATUS, Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ))

    def test_inequality(self):
        self.assertNotEqual(self.STATUS, [
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))

    def test_composability(self):
        self.assertEqual(
            Choices(
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + Choices(
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )

        self.assertEqual(
            Choices(
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + (
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )

        self.assertEqual(
            (
                (0, 'DRAFT', 'is draft'),
                (1, 'PUBLISHED', 'is published')
            ) + Choices(
                (2, 'DELETED', 'is deleted'),
            ),
            self.STATUS
        )

    def test_option_groups(self):
        c = Choices(
            ('group a', [(1, 'ONE', 'one'), (2, 'TWO', 'two')]),
            ['group b', ((3, 'THREE', 'three'),)]
        )
        self.assertEqual(
            list(c),
            [
                ('group a', [(1, 'one'), (2, 'two')]),
                ('group b', [(3, 'three')]),
            ],
        )
