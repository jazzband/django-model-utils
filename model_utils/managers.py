from __future__ import unicode_literals
import django
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError: # Django < 1.5
    from django.db.models.sql.constants import LOOKUP_SEP



class InheritanceQuerySet(QuerySet):
    def select_subclasses(self, *subclasses):
        if not subclasses:
            # only recurse one level on Django < 1.6 to avoid triggering
            # https://code.djangoproject.com/ticket/16572
            levels = None
            if django.VERSION < (1, 6, 0):
                levels = 1
            subclasses = self._get_subclasses_recurse(self.model, levels=levels)
        # workaround https://code.djangoproject.com/ticket/16855
        field_dict = self.query.select_related
        new_qs = self.select_related(*subclasses)
        if isinstance(new_qs.query.select_related, dict) and isinstance(field_dict, dict):
            new_qs.query.select_related.update(field_dict)
        new_qs.subclasses = subclasses
        return new_qs


    def _clone(self, klass=None, setup=False, **kwargs):
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                kwargs[name] = getattr(self, name)
        return super(InheritanceQuerySet, self)._clone(klass, setup, **kwargs)


    def annotate(self, *args, **kwargs):
        qset = super(InheritanceQuerySet, self).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset


    def iterator(self):
        iter = super(InheritanceQuerySet, self).iterator()
        if getattr(self, 'subclasses', False):
            for obj in iter:
                sub_obj = None
                for s in self.subclasses:
                    sub_obj = self._get_sub_obj_recurse(obj, s)
                    if sub_obj:
                        break
                if not sub_obj:
                    sub_obj = obj

                if getattr(self, '_annotated', False):
                    for k in self._annotated:
                        setattr(sub_obj, k, getattr(obj, k))

                yield sub_obj
        else:
            for obj in iter:
                yield obj


    def _get_subclasses_recurse(self, model, levels=None):
        rels = [rel for rel in model._meta.get_all_related_objects()
                      if isinstance(rel.field, OneToOneField)
                      and issubclass(rel.field.model, model)]
        subclasses = []
        if levels:
            levels -= 1
        for rel in rels:
            if levels or levels is None:
                for subclass in self._get_subclasses_recurse(
                        rel.field.model, levels=levels):
                    subclasses.append(rel.var_name + LOOKUP_SEP + subclass)
            subclasses.append(rel.var_name)
        return subclasses


    def _get_sub_obj_recurse(self, obj, s):
        rel, _, s = s.partition(LOOKUP_SEP)
        try:
            node = getattr(obj, rel)
        except ObjectDoesNotExist:
            return None
        if s:
            child = self._get_sub_obj_recurse(node, s)
            return child
        else:
            return node



class InheritanceManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return InheritanceQuerySet(self.model)

    def select_subclasses(self, *subclasses):
        return self.get_query_set().select_subclasses(*subclasses)

    def get_subclass(self, *args, **kwargs):
        return self.get_query_set().select_subclasses().get(*args, **kwargs)



class QueryManager(models.Manager):
    use_for_related_fields = True

    def __init__(self, *args, **kwargs):
        if args:
            self._q = args[0]
        else:
            self._q = models.Q(**kwargs)
        self._order_by = None
        super(QueryManager, self).__init__()

    def order_by(self, *args):
        self._order_by = args
        return self

    def get_query_set(self):
        qs = super(QueryManager, self).get_query_set().filter(self._q)
        if self._order_by is not None:
            return qs.order_by(*self._order_by)
        return qs


class PassThroughManager(models.Manager):
    """
    Inherit from this Manager to enable you to call any methods from your
    custom QuerySet class from your manager. Simply define your QuerySet
    class, and return an instance of it from your manager's `get_query_set`
    method.

    Alternately, if you don't need any extra methods on your manager that
    aren't on your QuerySet, then just pass your QuerySet class to the
    ``for_queryset_class`` class method.

    class PostQuerySet(QuerySet):
        def enabled(self):
            return self.filter(disabled=False)

    class Post(models.Model):
        objects = PassThroughManager.for_queryset_class(PostQuerySet)()

    """
    # pickling causes recursion errors
    _deny_methods = ['__getstate__', '__setstate__', '__getinitargs__',
                     '__getnewargs__', '__copy__', '__deepcopy__', '_db']

    def __init__(self, queryset_cls=None):
        self._queryset_cls = queryset_cls
        super(PassThroughManager, self).__init__()

    def __getattr__(self, name):
        if name in self._deny_methods:
            raise AttributeError(name)
        return getattr(self.get_query_set(), name)

    def get_query_set(self):
        qs = super(PassThroughManager, self).get_query_set()
        if self._queryset_cls is not None:
            qs = qs._clone(klass=self._queryset_cls)
        return qs

    @classmethod
    def for_queryset_class(cls, queryset_cls):
        return create_pass_through_manager_for_queryset_class(cls, queryset_cls)


def create_pass_through_manager_for_queryset_class(base, queryset_cls):
    class _PassThroughManager(base):
        def __init__(self):
            return super(_PassThroughManager, self).__init__()

        def get_query_set(self):
            qs = super(_PassThroughManager, self).get_query_set()
            return qs._clone(klass=queryset_cls)

        def __reduce__(self):
            # our pickling support breaks for subclasses (e.g. RelatedManager)
            if self.__class__ is not _PassThroughManager:
                return super(_PassThroughManager, self).__reduce__()
            return (
                unpickle_pass_through_manager_for_queryset_class,
                (base, queryset_cls),
                self.__dict__,
                )

    return _PassThroughManager


def unpickle_pass_through_manager_for_queryset_class(base, queryset_cls):
    cls = create_pass_through_manager_for_queryset_class(base, queryset_cls)
    return cls.__new__(cls)
