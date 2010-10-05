from types import ClassType

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.manager import Manager
from django.db.models.query import QuerySet


class InheritanceCastMixin(object):
    def cast(self):
        results = tuple(self.values_list('pk', 'real_type'))
        type_to_pks = {}
        for pk, real_type_id in results:
            type_to_pks.setdefault(real_type_id, []).append(pk)
        content_types = ContentType.objects.in_bulk(type_to_pks.keys())
        pk_to_child = {}
        for real_type_id, pks in type_to_pks.iteritems():
            content_type = content_types[real_type_id]
            child_type = content_type.model_class()
            children = child_type._default_manager.in_bulk(pks)
            for pk, child in children.iteritems():
                pk_to_child[pk] = child
        children = []
        # sort children into same order as parents where returned
        for pk, real_type_id in results:
            children.append(pk_to_child[pk])
        return children


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
    # collect separately the mixin classes and methods
    bases = [kwds.get('queryset_cls', QuerySet)]
    methods = {}
    for mixin in mixins:
        if isinstance(mixin, (ClassType, type)):
            bases.append(mixin)
        else:
            try: methods[mixin.__name__] = mixin
            except AttributeError:
                raise TypeError('Mixin must be class or function, not %s' %
                                mixin.__class__)
    # create the QuerySet subclass
    id = hash(mixins + tuple(kwds.iteritems()))
    new_queryset_cls = type('Queryset_%d' % id, tuple(bases), methods)
    # create the Manager subclass
    bases[0] = manager_cls = kwds.get('manager_cls', Manager)
    new_manager_cls = type('Manager_%d' % id, tuple(bases), methods)
    # and finally override new manager's get_query_set
    super_get_query_set = manager_cls.get_query_set
    def get_query_set(self):
        # first honor the super manager's get_query_set
        qs = super_get_query_set(self)
        # and then try to bless the returned queryset by reassigning it to the
        # newly created Queryset class, though this may not be feasible
        if not issubclass(new_queryset_cls, qs.__class__):
            raise TypeError('QuerySet subclass conflict: cannot determine a '
                            'unique class for queryset instance')
        qs.__class__ = new_queryset_cls
        return qs
    new_manager_cls.get_query_set = get_query_set
    return new_manager_cls()
