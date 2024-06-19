from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

import pytest
from django.test import TestCase

from model_utils import Choices

T = TypeVar("T")


class ChoicesTestsMixin(Generic[T]):

    STATUS: Choices[T]

    def test_getattr(self) -> None:
        assert self.STATUS.DRAFT == 'DRAFT'

    def test_len(self) -> None:
        assert len(self.STATUS) == 2

    def test_repr(self) -> None:
        assert repr(self.STATUS) == "Choices" + repr((
            ('DRAFT', 'DRAFT', 'DRAFT'),
            ('PUBLISHED', 'PUBLISHED', 'PUBLISHED'),
        ))

    def test_wrong_length_tuple(self) -> None:
        with pytest.raises(ValueError):
            Choices(('a',))  # type: ignore[arg-type]

    def test_deepcopy(self) -> None:
        import copy
        assert list(self.STATUS) == list(copy.deepcopy(self.STATUS))

    def test_equality(self) -> None:
        assert self.STATUS == Choices('DRAFT', 'PUBLISHED')

    def test_inequality(self) -> None:
        assert self.STATUS != ['DRAFT', 'PUBLISHED']
        assert self.STATUS != Choices('DRAFT')

    def test_composability(self) -> None:
        assert Choices('DRAFT') + Choices('PUBLISHED') == self.STATUS
        assert Choices('DRAFT') + ('PUBLISHED',) == self.STATUS
        assert ('DRAFT',) + Choices('PUBLISHED') == self.STATUS

    def test_option_groups(self) -> None:
        # Note: The implementation accepts any kind of sequence, but the type system can only
        #       track per-index types for tuples.
        if TYPE_CHECKING:
            c = Choices(('group a', ['one', 'two']), ('group b', ('three',)))
        else:
            c = Choices(('group a', ['one', 'two']), ['group b', ('three',)])
        assert list(c) == [
            ('group a', [('one', 'one'), ('two', 'two')]),
            ('group b', [('three', 'three')]),
        ]


class ChoicesTests(TestCase, ChoicesTestsMixin[str]):
    def setUp(self) -> None:
        self.STATUS = Choices('DRAFT', 'PUBLISHED')

    def test_indexing(self) -> None:
        self.assertEqual(self.STATUS['PUBLISHED'], 'PUBLISHED')

    def test_iteration(self) -> None:
        self.assertEqual(tuple(self.STATUS),
                         (('DRAFT', 'DRAFT'), ('PUBLISHED', 'PUBLISHED')))

    def test_reversed(self) -> None:
        self.assertEqual(tuple(reversed(self.STATUS)),
                         (('PUBLISHED', 'PUBLISHED'), ('DRAFT', 'DRAFT')))

    def test_contains_value(self) -> None:
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)

    def test_doesnt_contain_value(self) -> None:
        self.assertFalse('UNPUBLISHED' in self.STATUS)


class LabelChoicesTests(TestCase, ChoicesTestsMixin[str]):
    def setUp(self) -> None:
        self.STATUS = Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        )

    def test_iteration(self) -> None:
        self.assertEqual(tuple(self.STATUS), (
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            ('DELETED', 'DELETED'),
        ))

    def test_reversed(self) -> None:
        self.assertEqual(tuple(reversed(self.STATUS)), (
            ('DELETED', 'DELETED'),
            ('PUBLISHED', 'is published'),
            ('DRAFT', 'is draft'),
        ))

    def test_indexing(self) -> None:
        self.assertEqual(self.STATUS['PUBLISHED'], 'is published')

    def test_default(self) -> None:
        self.assertEqual(self.STATUS.DELETED, 'DELETED')

    def test_provided(self) -> None:
        self.assertEqual(self.STATUS.DRAFT, 'DRAFT')

    def test_len(self) -> None:
        self.assertEqual(len(self.STATUS), 3)

    def test_equality(self) -> None:
        self.assertEqual(self.STATUS, Choices(
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED',
        ))

    def test_inequality(self) -> None:
        self.assertNotEqual(self.STATUS, [
            ('DRAFT', 'is draft'),
            ('PUBLISHED', 'is published'),
            'DELETED'
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))

    def test_repr(self) -> None:
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            ('DRAFT', 'DRAFT', 'is draft'),
            ('PUBLISHED', 'PUBLISHED', 'is published'),
            ('DELETED', 'DELETED', 'DELETED'),
        )))

    def test_contains_value(self) -> None:
        self.assertTrue('PUBLISHED' in self.STATUS)
        self.assertTrue('DRAFT' in self.STATUS)
        # This should be True, because both the display value
        # and the internal representation are both DELETED.
        self.assertTrue('DELETED' in self.STATUS)

    def test_doesnt_contain_value(self) -> None:
        self.assertFalse('UNPUBLISHED' in self.STATUS)

    def test_doesnt_contain_display_value(self) -> None:
        self.assertFalse('is draft' in self.STATUS)

    def test_composability(self) -> None:
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

    def test_option_groups(self) -> None:
        if TYPE_CHECKING:
            c = Choices[int](
                ('group a', [(1, 'one'), (2, 'two')]),
                ('group b', ((3, 'three'),))
            )
        else:
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


class IdentifierChoicesTests(TestCase, ChoicesTestsMixin[int]):
    def setUp(self) -> None:
        self.STATUS = Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'))

    def test_iteration(self) -> None:
        self.assertEqual(tuple(self.STATUS), (
            (0, 'is draft'),
            (1, 'is published'),
            (2, 'is deleted'),
        ))

    def test_reversed(self) -> None:
        self.assertEqual(tuple(reversed(self.STATUS)), (
            (2, 'is deleted'),
            (1, 'is published'),
            (0, 'is draft'),
        ))

    def test_indexing(self) -> None:
        self.assertEqual(self.STATUS[1], 'is published')

    def test_getattr(self) -> None:
        self.assertEqual(self.STATUS.DRAFT, 0)

    def test_len(self) -> None:
        self.assertEqual(len(self.STATUS), 3)

    def test_repr(self) -> None:
        self.assertEqual(repr(self.STATUS), "Choices" + repr((
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted'),
        )))

    def test_contains_value(self) -> None:
        self.assertTrue(0 in self.STATUS)
        self.assertTrue(1 in self.STATUS)
        self.assertTrue(2 in self.STATUS)

    def test_doesnt_contain_value(self) -> None:
        self.assertFalse(3 in self.STATUS)

    def test_doesnt_contain_display_value(self) -> None:
        self.assertFalse('is draft' in self.STATUS)  # type: ignore[operator]

    def test_doesnt_contain_python_attr(self) -> None:
        self.assertFalse('PUBLISHED' in self.STATUS)  # type: ignore[operator]

    def test_equality(self) -> None:
        self.assertEqual(self.STATUS, Choices(
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ))

    def test_inequality(self) -> None:
        self.assertNotEqual(self.STATUS, [
            (0, 'DRAFT', 'is draft'),
            (1, 'PUBLISHED', 'is published'),
            (2, 'DELETED', 'is deleted')
        ])
        self.assertNotEqual(self.STATUS, Choices('DRAFT'))

    def test_composability(self) -> None:
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

    def test_option_groups(self) -> None:
        if TYPE_CHECKING:
            c = Choices[int](
                ('group a', [(1, 'ONE', 'one'), (2, 'TWO', 'two')]),
                ('group b', ((3, 'THREE', 'three'),))
            )
        else:
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


class SubsetChoicesTest(TestCase):

    def setUp(self) -> None:
        self.choices = Choices[int](
            (0, 'a', 'A'),
            (1, 'b', 'B'),
        )

    def test_nonexistent_identifiers_raise(self) -> None:
        with self.assertRaises(ValueError):
            self.choices.subset('a', 'c')

    def test_solo_nonexistent_identifiers_raise(self) -> None:
        with self.assertRaises(ValueError):
            self.choices.subset('c')

    def test_empty_subset_passes(self) -> None:
        subset = self.choices.subset()

        self.assertEqual(subset, Choices())

    def test_subset_returns_correct_subset(self) -> None:
        subset = self.choices.subset('a')

        self.assertEqual(subset, Choices((0, 'a', 'A')))
