from types import ClassType

from django.db import models
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

class QueryManager(models.Manager):
    def __init__(self, *args, **kwargs):
        if args:
            self._q = args[0]
        else:
            self._q = models.Q(**kwargs)
        super(QueryManager, self).__init__()

    def order_by(self, *args):
        self._order_by = args
        return self

    def get_query_set(self):
        qs = super(QueryManager, self).get_query_set().filter(self._q)
        if hasattr(self, '_order_by'):
            return qs.order_by(*self._order_by)
        return qs


def manager_from(*mixins, **kwds):
    '''
    Returns a Manager instance with extra methods, also available and
    chainable on generated querysets.

    (By George Sakkis, originally posted at
    http://djangosnippets.org/snippets/2117/)

    :param mixins: Each ``mixin`` can be either a class or a function. The
        generated manager and associated queryset subclasses extend the mixin
        classes and include the mixin functions (as methods).

    :keyword queryset_cls: The base queryset class to extend from
        (``django.db.models.query.QuerySet`` by default).

    :keyword manager_cls: The base manager class to extend from
        (``django.db.models.manager.Manager`` by default).
    '''
    bases = [kwds.get('queryset_cls', QuerySet)]
    attrs = {}
    for mixin in mixins:
        if isinstance(mixin, (ClassType, type)):
            bases.append(mixin)
        else:
            try: attrs[mixin.__name__] = mixin
            except AttributeError:
                raise TypeError('Mixin must be class or function, not %s' %
                                mixin.__class__)
    # create the QuerySet subclass
    id = hash(mixins + tuple(kwds.iteritems()))
    qset_cls = type('Queryset_%d' % id, tuple(bases), attrs)
    # create the Manager subclass
    bases[0] = kwds.get('manager_cls', Manager)
    def _get_query_set(self):
        if hasattr(self, '_db'):
            return qset_cls(self.model, using=self._db)
        else:
            return qset_cls(self.model)
    attrs['get_query_set'] = _get_query_set
    manager_cls = type('Manager_%d' % id, tuple(bases), attrs)
    return manager_cls()
