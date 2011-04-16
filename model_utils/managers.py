from types import ClassType
import warnings

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

class InheritanceQuerySet(QuerySet):
    def select_subclasses(self, *subclasses):
        if not subclasses:
            subclasses = [rel.var_name for rel in self.model._meta.get_all_related_objects()
                          if isinstance(rel.field, OneToOneField)
                          and issubclass(rel.field.model, self.model)]
        new_qs = self.select_related(*subclasses)
        new_qs.subclasses = subclasses
        return new_qs

    def _clone(self, klass=None, setup=False, **kwargs):
        try:
            kwargs.update({'subclasses': self.subclasses})
        except AttributeError:
            pass
        return super(InheritanceQuerySet, self)._clone(klass, setup, **kwargs)

    def iterator(self):
        iter = super(InheritanceQuerySet, self).iterator()
        if getattr(self, 'subclasses', False):
            for obj in iter:
                obj = [getattr(obj, s) for s in self.subclasses if getattr(obj, s)] or [obj]
                yield obj[0]
        else:
            for obj in iter:
                yield obj

class InheritanceManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return InheritanceQuerySet(self.model)

    def select_subclasses(self, *subclasses):
        return self.get_query_set().select_subclasses(*subclasses)


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


class PassThroughManager(models.Manager):
    """
    Inherit from this Manager to enable you to call any methods from your
    custom QuerySet class from your manager. Simply define your QuerySet
    class, and return an instance of it from your manager's `get_query_set`
    method.

    Alternately, if you don't need any extra methods on your manager that
    aren't on your QuerySet, then just pass your QuerySet class to this
    class' constructer.

    class PostQuerySet(QuerySet):
        def enabled(self):
            return self.filter(disabled=False)

    class Post(models.Model):
        objects = PassThroughManager(PostQuerySet)

    """
    # pickling causes recursion errors
    _deny_methods = ['__getstate__', '__setstate__', '_db']

    def __init__(self, queryset_cls=None):
        self._queryset_cls = queryset_cls
        super(PassThroughManager, self).__init__()

    def __getattr__(self, name):
        if name in self._deny_methods:
            raise AttributeError(name)
        return getattr(self.get_query_set(), name)

    def get_query_set(self):
        if self._queryset_cls is not None:
            kargs = {'model': self.model}
            if hasattr(self, '_db'):
                kargs['using'] = self._db
            return self._queryset_cls(**kargs)
        return super(PassThroughManager, self).get_query_set()


def manager_from(*mixins, **kwds):
    """
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

    """
    warnings.warn(
        "manager_from is pending deprecation; use PassThroughManager instead.",
        PendingDeprecationWarning,
        stacklevel=2)
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
