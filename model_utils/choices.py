from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast, overload

T = TypeVar("T")

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    # The type aliases defined here are evaluated when the django-stubs mypy plugin
    # loads this module, so they must be able to execute under the lowest supported
    # Python VM:
    # - typing.List, typing.Tuple become obsolete in Pyton 3.9
    # - typing.Union becomes obsolete in Pyton 3.10
    from typing import List, Tuple, Union

    from django_stubs_ext import StrOrPromise

    # The type argument 'T' to 'Choices' is the database representation type.
    _Double = Tuple[T, StrOrPromise]
    _Triple = Tuple[T, str, StrOrPromise]
    _Group = Tuple[StrOrPromise, Sequence["_Choice[T]"]]
    _Choice = Union[_Double[T], _Triple[T], _Group[T]]
    # Choices can only be given as a single string if 'T' is 'str'.
    _GroupStr = Tuple[StrOrPromise, Sequence["_ChoiceStr"]]
    _ChoiceStr = Union[str, _Double[str], _Triple[str], _GroupStr]
    # Note that we only accept lists and tuples in groups, not arbitrary sequences.
    # However, annotating it as such causes many problems.

    _DoubleRead = Union[_Double[T], Tuple[StrOrPromise, Iterable["_DoubleRead[T]"]]]
    _DoubleCollector = List[Union[_Double[T], Tuple[StrOrPromise, "_DoubleCollector[T]"]]]
    _TripleCollector = List[Union[_Triple[T], Tuple[StrOrPromise, "_TripleCollector[T]"]]]


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
    def __init__(self, *choices: _Choice[T]):
        ...

    def __init__(self, *choices: _ChoiceStr | _Choice[T]):
        # list of choices expanded to triples - can include optgroups
        self._triples: _TripleCollector[T] = []
        # list of choices as (db, human-readable) - can include optgroups
        self._doubles: _DoubleCollector[T] = []
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
        triple_collector: _TripleCollector[T],
        double_collector: _DoubleCollector[T]
    ) -> None:
        self._identifier_map[triple[1]] = triple[0]
        self._display_map[triple[0]] = triple[2]
        self._db_values.add(triple[0])
        triple_collector.append(triple)
        double_collector.append((triple[0], triple[2]))

    def _process(
        self,
        choices: Iterable[_ChoiceStr | _Choice[T]],
        triple_collector: _TripleCollector[T] | None = None,
        double_collector: _DoubleCollector[T] | None = None
    ) -> None:
        if triple_collector is None:
            triple_collector = self._triples
        if double_collector is None:
            double_collector = self._doubles

        def store(c: tuple[Any, str, StrOrPromise]) -> None:
            self._store(c, triple_collector, double_collector)

        for choice in choices:
            # The type inference is not very accurate here:
            # - we lied in the type aliases, stating groups contain an arbitrary Sequence
            #   rather than only list or tuple
            # - there is no way to express that _ChoiceStr is only used when T=str
            # - mypy 1.9.0 doesn't narrow types based on the value of len()
            if isinstance(choice, (list, tuple)):
                if len(choice) == 3:
                    store(choice)
                elif len(choice) == 2:
                    if isinstance(choice[1], (list, tuple)):
                        # option group
                        group_name = choice[0]
                        subchoices = choice[1]
                        tc: _TripleCollector[T] = []
                        triple_collector.append((group_name, tc))
                        dc: _DoubleCollector[T] = []
                        double_collector.append((group_name, dc))
                        self._process(subchoices, tc, dc)
                    else:
                        store((choice[0], cast(str, choice[0]), cast('StrOrPromise', choice[1])))
                else:
                    raise ValueError(
                        "Choices can't take a list of length %s, only 2 or 3"
                        % len(choice)
                    )
            else:
                store((choice, choice, choice))

    def __len__(self) -> int:
        return len(self._doubles)

    def __iter__(self) -> Iterator[_DoubleRead[T]]:
        return iter(self._doubles)

    def __reversed__(self) -> Iterator[_DoubleRead[T]]:
        return reversed(self._doubles)

    def __getattr__(self, attname: str) -> T:
        try:
            return self._identifier_map[attname]
        except KeyError:
            raise AttributeError(attname)

    def __getitem__(self, key: T) -> StrOrPromise | Sequence[_Triple[T]]:
        return self._display_map[key]

    @overload
    def __add__(self: Choices[str], other: Choices[str] | Iterable[_ChoiceStr]) -> Choices[str]:
        ...

    @overload
    def __add__(self, other: Choices[T] | Iterable[_Choice[T]]) -> Choices[T]:
        ...

    def __add__(self, other: Choices[Any] | Iterable[_ChoiceStr | _Choice[Any]]) -> Choices[Any]:
        other_args: list[Any]
        if isinstance(other, self.__class__):
            other_args = other._triples
        else:
            other_args = list(other)
        return Choices(*(self._triples + other_args))

    @overload
    def __radd__(self: Choices[str], other: Iterable[_ChoiceStr]) -> Choices[str]:
        ...

    @overload
    def __radd__(self, other: Iterable[_Choice[T]]) -> Choices[T]:
        ...

    def __radd__(self, other: Iterable[_ChoiceStr] | Iterable[_Choice[T]]) -> Choices[Any]:
        # radd is never called for matching types, so we don't check here
        other_args = list(other)
        # The exact type of 'other' depends on our type argument 'T', which
        # is expressed in the overloading, but lost within this method body.
        return Choices(*(other_args + self._triples))  # type: ignore[arg-type]

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
        args: list[Any] = copy.deepcopy(self._triples, memo)
        return self.__class__(*args)

    def subset(self, *new_identifiers: str) -> Choices[T]:
        identifiers = set(self._identifier_map.keys())

        if not identifiers.issuperset(new_identifiers):
            raise ValueError(
                'The following identifiers are not present: %s' %
                identifiers.symmetric_difference(new_identifiers),
            )

        args: list[Any] = [
            choice for choice in self._triples
            if choice[1] in new_identifiers
        ]
        return self.__class__(*args)
