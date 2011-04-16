from django import VERSION
if VERSION < (1, 2):
    import warnings
    warnings.warn(
        "Django 1.1 support in django-model-utils is pending deprecation.",
        PendingDeprecationWarning)



class ChoiceEnum(object):
    """
    DEPRECATED: Use ``Choices`` (below) instead. This class has less
    flexibility for human-readable display, and greater potential for
    surprising data corruption if new choices are inserted in the
    middle of the list. Automatic assignment of numeric IDs is not
    such a great idea after all.

    A class to encapsulate handy functionality for lists of choices
    for a Django model field.

    Accepts verbose choice names as arguments, and automatically
    assigns numeric keys to them. When iterated over, behaves as the
    standard Django choices list of two-tuples.

    Attribute access allows conversion of verbose choice name to
    choice key, dictionary access the reverse.

    Example:

    >>> STATUS = ChoiceEnum('DRAFT', 'PUBLISHED')
    >>> STATUS.DRAFT
    0
    >>> STATUS[1]
    'PUBLISHED'
    >>> tuple(STATUS)
    ((0, 'DRAFT'), (1, 'PUBLISHED'))

    """
    def __init__(self, *choices):
        import warnings
        warnings.warn("ChoiceEnum is deprecated, use Choices instead.",
                      DeprecationWarning)
        self._choices = tuple(enumerate(choices))
        self._choice_dict = dict(self._choices)
        self._reverse_dict = dict(((i[1], i[0]) for i in self._choices))

    def __iter__(self):
        return iter(self._choices)

    def __getattr__(self, attname):
        try:
            return self._reverse_dict[attname]
        except KeyError:
            raise AttributeError(attname)

    def __getitem__(self, key):
        return self._choice_dict[key]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           ', '.join(("'%s'" % i[1] for i in self._choices)))


class Choices(object):
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

    """

    def __init__(self, *choices):
        self._full = []
        self._choices = []
        self._choice_dict = {}
        for choice in self.equalize(choices):
            self._full.append(choice)
            self._choices.append((choice[0], choice[2]))
            self._choice_dict[choice[1]] = choice[0]

    def equalize(self, choices):
        for choice in choices:
            if isinstance(choice, (list, tuple)):
                if len(choice) == 3:
                    yield choice
                elif len(choice) == 2:
                    yield (choice[0], choice[0], choice[1])
                else:
                    raise ValueError("Choices can't handle a list/tuple of length %s, only 2 or 3"
                                     % len(choice))
            else:
                yield (choice, choice, choice)

    def __iter__(self):
        return iter(self._choices)

    def __getattr__(self, attname):
        try:
            return self._choice_dict[attname]
        except KeyError:
            raise AttributeError(attname)

    def __getitem__(self, index):
        return self._choices[index]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__,
                          ', '.join(("%s" % str(i) for i in self._full)))
