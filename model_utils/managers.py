from __future__ import unicode_literals
import django
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

try:
    from django.db.models.constants import LOOKUP_SEP
    from django.utils.six import string_types
except ImportError: # Django < 1.5
    from django.db.models.sql.constants import LOOKUP_SEP
    string_types = (basestring,)


class InheritanceQuerySetMixin(object):
    def select_subclasses(self, *subclasses):
        levels = self._get_maximum_depth()
        calculated_subclasses = self._get_subclasses_recurse(
            self.model, levels=levels)
        # if none were passed in, we can just short circuit and select all
        if not subclasses:
            subclasses = calculated_subclasses
        else:
            verified_subclasses = []
            for subclass in subclasses:
                # special case for passing in the same model as the queryset
                # is bound against. Rather than raise an error later, we know
                # we can allow this through.
                if subclass is self.model:
                    continue

                if not isinstance(subclass, string_types):
                    subclass = self._get_ancestors_path(
                        subclass, levels=levels)

                if subclass in calculated_subclasses:
                    verified_subclasses.append(subclass)
                else:
                    raise ValueError(
                        '%r is not in the discovered subclasses, tried: %s' % (
                            subclass, ', '.join(calculated_subclasses))
                        )
            subclasses = verified_subclasses

        # workaround https://code.djangoproject.com/ticket/16855
        previous_select_related = self.query.select_related
        new_qs = self.select_related(*subclasses)
        previous_is_dict = isinstance(previous_select_related, dict)
        new_is_dict = isinstance(new_qs.query.select_related, dict)
        if previous_is_dict and new_is_dict:
            new_qs.query.select_related.update(previous_select_related)
        new_qs.subclasses = subclasses
        return new_qs


    def _clone(self, klass=None, setup=False, **kwargs):
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                kwargs[name] = getattr(self, name)
        return super(InheritanceQuerySetMixin, self)._clone(klass, setup, **kwargs)


    def annotate(self, *args, **kwargs):
        qset = super(InheritanceQuerySetMixin, self).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset


    def iterator(self):
        iter = super(InheritanceQuerySetMixin, self).iterator()
        if getattr(self, 'subclasses', False):
            extras = tuple(self.query.extra.keys())
            # sort the subclass names longest first,
            # so with 'a' and 'a__b' it goes as deep as possible
            subclasses = sorted(self.subclasses, key=len, reverse=True)
            for obj in iter:
                sub_obj = None
                for s in subclasses:
                    sub_obj = self._get_sub_obj_recurse(obj, s)
                    if sub_obj:
                        break
                if not sub_obj:
                    sub_obj = obj

                if getattr(self, '_annotated', False):
                    for k in self._annotated:
                        setattr(sub_obj, k, getattr(obj, k))

                for k in extras:
                    setattr(sub_obj, k, getattr(obj, k))

                yield sub_obj
        else:
            for obj in iter:
                yield obj


    def _get_subclasses_recurse(self, model, levels=None):
        """
        Given a Model class, find all related objects, exploring children
        recursively, returning a `list` of strings representing the
        relations for select_related
        """
        rels = [
            rel for rel in model._meta.get_all_related_objects()
            if isinstance(rel.field, OneToOneField)
            and issubclass(rel.field.model, model)
            and model is not rel.field.model
            ]
        subclasses = []
        if levels:
            levels -= 1
        for rel in rels:
            if levels or levels is None:
                for subclass in self._get_subclasses_recurse(
                        rel.field.model, levels=levels):
                    subclasses.append(rel.get_accessor_name() + LOOKUP_SEP + subclass)
            subclasses.append(rel.get_accessor_name())
        return subclasses


    def _get_ancestors_path(self, model, levels=None):
        """
        Serves as an opposite to _get_subclasses_recurse, instead walking from
        the Model class up the Model's ancestry and constructing the desired
        select_related string backwards.
        """
        if not issubclass(model, self.model):
            raise ValueError("%r is not a subclass of %r" % (model, self.model))

        ancestry = []
        # should be a OneToOneField or None
        parent = model._meta.get_ancestor_link(self.model)
        if levels:
            levels -= 1
        while parent is not None:
            ancestry.insert(0, parent.related.get_accessor_name())
            if levels or levels is None:
                parent = parent.related.parent_model._meta.get_ancestor_link(
                    self.model)
            else:
                parent = None
        return LOOKUP_SEP.join(ancestry)


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

    def get_subclass(self, *args, **kwargs):
        return self.select_subclasses().get(*args, **kwargs)

    def _get_maximum_depth(self):
        """
        Under Django versions < 1.6, to avoid triggering
        https://code.djangoproject.com/ticket/16572 we can only look
        as far as children.
        """
        levels = None
        if django.VERSION < (1, 6, 0):
            levels = 1
        return levels

class InheritanceManagerMixin(object):
    use_for_related_fields = True

    def get_queryset(self):
        return InheritanceQuerySet(self.model)

    get_query_set = get_queryset

    def select_subclasses(self, *subclasses):
        return self.get_queryset().select_subclasses(*subclasses)

    def get_subclass(self, *args, **kwargs):
        return self.get_queryset().get_subclass(*args, **kwargs)


class InheritanceQuerySet(InheritanceQuerySetMixin, QuerySet):
    pass

class InheritanceManager(InheritanceManagerMixin, models.Manager):
    pass


class QueryManagerMixin(object):
    use_for_related_fields = True

    def __init__(self, *args, **kwargs):
        if args:
            self._q = args[0]
        else:
            self._q = models.Q(**kwargs)
        self._order_by = None
        super(QueryManagerMixin, self).__init__()

    def order_by(self, *args):
        self._order_by = args
        return self

    def get_queryset(self):
        try:
            qs = super(QueryManagerMixin, self).get_queryset().filter(self._q)
        except AttributeError:
            qs = super(QueryManagerMixin, self).get_query_set().filter(self._q)
        if self._order_by is not None:
            return qs.order_by(*self._order_by)
        return qs

    get_query_set = get_queryset


class QueryManager(QueryManagerMixin, models.Manager):
    pass


class PassThroughManagerMixin(object):
    """
    A mixin that enables you to call custom QuerySet methods from your manager.
    """

    # pickling causes recursion errors
    _deny_methods = ['__getstate__', '__setstate__', '__getinitargs__',
                     '__getnewargs__', '__copy__', '__deepcopy__', '_db',
                     '__slots__']

    def __init__(self, queryset_cls=None):
        self._queryset_cls = queryset_cls
        super(PassThroughManagerMixin, self).__init__()

    def __getattr__(self, name):
        if name in self._deny_methods:
            raise AttributeError(name)
        if django.VERSION < (1, 6, 0):
            return getattr(self.get_query_set(), name)
        return getattr(self.get_queryset(), name)

    def __dir__(self):
        """
        Allow introspection via dir() and ipythonesque tab-discovery.

        We do dir(type(self)) because to do dir(self) would be a recursion
        error.
        We call dir(self.get_query_set()) because it is possible that the
        queryset returned by get_query_set() is interesting, even if
        self._queryset_cls is None.
        """
        my_values = frozenset(dir(type(self)))
        my_values |= frozenset(dir(self.get_query_set()))
        return list(my_values)

    def get_queryset(self):
        try:
            qs = super(PassThroughManagerMixin, self).get_queryset()
        except AttributeError:
            qs = super(PassThroughManagerMixin, self).get_query_set()
        if self._queryset_cls is not None:
            qs = qs._clone(klass=self._queryset_cls)
        return qs

    get_query_set = get_queryset

    @classmethod
    def for_queryset_class(cls, queryset_cls):
        return create_pass_through_manager_for_queryset_class(cls, queryset_cls)


class PassThroughManager(PassThroughManagerMixin, models.Manager):
    """
    Inherit from this Manager to enable you to call any methods from your
    custom QuerySet class from your manager. Simply define your QuerySet
    class, and return an instance of it from your manager's `get_queryset`
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
    pass


def create_pass_through_manager_for_queryset_class(base, queryset_cls):
    class _PassThroughManager(base):
        def __init__(self, *args, **kwargs):
            return super(_PassThroughManager, self).__init__(*args, **kwargs)

        def get_queryset(self):
            qs = super(_PassThroughManager, self).get_queryset()
            return qs._clone(klass=queryset_cls)

        get_query_set = get_queryset

    return _PassThroughManager
