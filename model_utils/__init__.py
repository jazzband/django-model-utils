class ChoiceEnum(object):
    """
    A class to encapsulate handy functionality for lists of choices
    for a Django model field.

    Accepts verbose choice names as arguments, and automatically
    assigns numeric keys to them. When iterated over, behaves as the
    standard Django choices tuple of two-tuples.

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
    

