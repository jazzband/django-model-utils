from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Generic, TypeVar, overload

T = TypeVar("T")

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    from django_stubs_ext import StrOrPromise

    _Double = tuple[T, StrOrPromise | Sequence["_Choice"]]
    _Triple = tuple[T, str, StrOrPromise | Sequence["_Choice"]]
    _Choice = str | _Double | _Triple
    _DoubleStr = tuple[str, StrOrPromise | Sequence["_ChoiceStr"]]
    _TripleStr = tuple[str, str, StrOrPromise | Sequence["_ChoiceStr"]]
    _ChoiceStr = str | _DoubleStr | _TripleStr


class Choices(Generic[T]):
    """
    A class to encapsulate handy functionality for lists of choices
    for a Django model field.

    Each argument to ``Choices`` is a choice, represented as either a
    string, a two-tuple, or a three-tuple.

    If a single string is provided, that string is used as the
    database representation of the choice as well as the
    human-readable presentation.

    If a two-tuple is provided, the first item is used as the database
    representation and the second the human-readable presentation.

    If a triple is provided, the first item is the database
    representation, the second a valid Python identifier that can be
    used as a readable label in code, and the third the human-readable
    presentation. This is most useful when the database representation
    must sacrifice readability for some reason: to achieve a specific
    ordering, to use an integer rather than a character field, etc.

    Regardless of what representation of each choice is originally
    given, when iterated over or indexed into, a ``Choices`` object
    behaves as the standard Django choices list of two-tuples.

    If the triple form is used, the Python identifier names can be
    accessed as attributes on the ``Choices`` object, returning the
    database representation. (If the single or two-tuple forms are
    used and the database representation happens to be a valid Python
    identifier, the database representation itself is available as an
    attribute on the ``Choices`` object, returning itself.)

    Option groups can also be used with ``Choices``; in that case each
    argument is a tuple consisting of the option group name and a list
    of options, where each option in the list is either a string, a
    two-tuple, or a triple as outlined above.

    """

    @overload
    def __init__(self: Choices[str], *choices: _ChoiceStr):
        ...

    @overload
    def __init__(self, *choices: _Choice):
        ...

    def __init__(self, *choices: _Choice):
        # list of choices expanded to triples - can include optgroups
        self._triples: list[_Triple[T]] = []
        # list of choices as (db, human-readable) - can include optgroups
        self._doubles: list[_Double[T]] = []
        # dictionary mapping db representation to human-readable
        self._display_map: dict[T, StrOrPromise | list[_Triple[T]]] = {}
        # dictionary mapping Python identifier to db representation
        self._identifier_map: dict[str, T] = {}
        # set of db representations
        self._db_values: set[T] = set()

        self._process(choices)

    def _store(
        self,
        triple: tuple[T, str, StrOrPromise],
        triple_collector: list[_Triple[T]],
        double_collector: list[_Double[T]]
    ) -> None:
        self._identifier_map[triple[1]] = triple[0]
        self._display_map[triple[0]] = triple[2]
        self._db_values.add(triple[0])
        triple_collector.append(triple)
        double_collector.append((triple[0], triple[2]))

    def _process(
        self,
        choices: Iterable[_Choice],
        triple_collector: list[_Triple] | None = None,
        double_collector: list[_Double] | None = None
    ) -> None:
        if triple_collector is None:
            triple_collector = self._triples
        if double_collector is None:
            double_collector = self._doubles

        store = lambda c: self._store(c, triple_collector, double_collector)

        for choice in choices:
            if isinstance(choice, (list, tuple)):
                if len(choice) == 3:
                    store(choice)
                elif len(choice) == 2:
                    if isinstance(choice[1], (list, tuple)):
                        # option group
                        group_name = choice[0]
                        subchoices = choice[1]
                        tc: list[_Triple] = []
                        triple_collector.append((group_name, tc))
                        dc: list[_Double] = []
                        double_collector.append((group_name, dc))
                        self._process(subchoices, tc, dc)
                    else:
                        store((choice[0], choice[0], choice[1]))
                else:
                    raise ValueError(
                        "Choices can't take a list of length %s, only 2 or 3"
                        % len(choice)
                    )
            else:
                store((choice, choice, choice))

    def __len__(self) -> int:
        return len(self._doubles)

    def __iter__(self) -> Iterator[_Double[T]]:
        return iter(self._doubles)

    def __reversed__(self) -> Iterator[_Double[T]]:
        return reversed(self._doubles)

    def __getattr__(self, attname: str) -> T:
        try:
            return self._identifier_map[attname]
        except KeyError:
            raise AttributeError(attname)

    def __getitem__(self, key: T) -> StrOrPromise | Sequence[_Triple]:
        return self._display_map[key]

    def __add__(self, other: Choices[T] | Iterable[_Choice]) -> Choices[T]:
        if isinstance(other, self.__class__):
            other = other._triples
        else:
            other = list(other)
        return Choices(*(self._triples + other))

    def __radd__(self, other: Iterable[_Choice]) -> Choices[T]:
        # radd is never called for matching types, so we don't check here
        other = list(other)
        return Choices(*(other + self._triples))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self._triples == other._triples
        return False

    def __repr__(self) -> str:
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join("%s" % repr(i) for i in self._triples)
        )

    def __contains__(self, item: T) -> bool:
        return item in self._db_values

    def __deepcopy__(self, memo: dict[int, Any] | None) -> Choices[T]:
        return self.__class__(*copy.deepcopy(self._triples, memo))

    def subset(self, *new_identifiers: str) -> Choices[T]:
        identifiers = set(self._identifier_map.keys())

        if not identifiers.issuperset(new_identifiers):
            raise ValueError(
                'The following identifiers are not present: %s' %
                identifiers.symmetric_difference(new_identifiers),
            )

        return self.__class__(*[
            choice for choice in self._triples
            if choice[1] in new_identifiers
        ])
