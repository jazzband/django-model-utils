from __future__ import unicode_literals
import django
from django.db import models
from django.db.models.fields.related import OneToOneField, OneToOneRel
from django.db.models.query import QuerySet
try:
    from django.db.models.query import BaseIterable, ModelIterable
except ImportError:
    # Django 1.8 does not have iterable classes
    BaseIterable, ModelIterable = object, object
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.constants import LOOKUP_SEP
from django.utils.six import string_types


class InheritanceIterable(ModelIterable):
    def __iter__(self):
        queryset = self.queryset
        iter = ModelIterable(queryset)
        if getattr(queryset, 'subclasses', False):
            extras = tuple(queryset.query.extra.keys())
            # sort the subclass names longest first,
            # so with 'a' and 'a__b' it goes as deep as possible
            subclasses = sorted(queryset.subclasses, key=len, reverse=True)
            for obj in iter:
                sub_obj = None
                for s in subclasses:
                    sub_obj = queryset._get_sub_obj_recurse(obj, s)
                    if sub_obj:
                        break
                if not sub_obj:
                    sub_obj = obj

                if getattr(queryset, '_annotated', False):
                    for k in queryset._annotated:
                        setattr(sub_obj, k, getattr(obj, k))

                for k in extras:
                    setattr(sub_obj, k, getattr(obj, k))

                yield sub_obj
        else:
            for obj in iter:
                yield obj


class InheritanceQuerySetMixin(object):
    def __init__(self, *args, **kwargs):
        super(InheritanceQuerySetMixin, self).__init__(*args, **kwargs)
        if django.VERSION > (1, 8):
            self._iterable_class = InheritanceIterable

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

    def _chain(self, **kwargs):
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                kwargs[name] = getattr(self, name)

        return super(InheritanceQuerySetMixin, self)._chain(**kwargs)

    def _clone(self, klass=None, setup=False, **kwargs):
        if django.VERSION >= (2, 0):
            return super(InheritanceQuerySetMixin, self)._clone()

        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                kwargs[name] = getattr(self, name)

        if django.VERSION < (1, 9):
            kwargs['klass'] = klass
            kwargs['setup'] = setup

        return super(InheritanceQuerySetMixin, self)._clone(**kwargs)

    def annotate(self, *args, **kwargs):
        qset = super(InheritanceQuerySetMixin, self).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset

    def iterator(self):
        # Maintained for Django 1.8 compatability
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
        if django.VERSION < (1, 8):
            related_objects = model._meta.get_all_related_objects()
        else:
            related_objects = [
                f for f in model._meta.get_fields()
                if isinstance(f, OneToOneRel)]

        rels = [
            rel for rel in related_objects
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
                    subclasses.append(
                        rel.get_accessor_name() + LOOKUP_SEP + subclass)
            subclasses.append(rel.get_accessor_name())
        return subclasses

    def _get_ancestors_path(self, model, levels=None):
        """
        Serves as an opposite to _get_subclasses_recurse, instead walking from
        the Model class up the Model's ancestry and constructing the desired
        select_related string backwards.
        """
        if not issubclass(model, self.model):
            raise ValueError(
                "%r is not a subclass of %r" % (model, self.model))

        ancestry = []
        # should be a OneToOneField or None
        parent_link = model._meta.get_ancestor_link(self.model)
        if levels:
            levels -= 1
        while parent_link is not None:
            if django.VERSION < (1, 9):
                related = parent_link.rel
            else:
                related = parent_link.remote_field
            ancestry.insert(0, related.get_accessor_name())
            if levels or levels is None:
                if django.VERSION < (1, 8):
                    parent_model = related.parent_model
                else:
                    parent_model = related.model
                parent_link = parent_model._meta.get_ancestor_link(
                    self.model)
            else:
                parent_link = None
        return LOOKUP_SEP.join(ancestry)

    def _get_sub_obj_recurse(self, obj, s):
        rel, _, s = s.partition(LOOKUP_SEP)

        # Django 1.9: If a primitive type gets passed to this recursive function,
        # return None as non-models are not part of inheritance.
        if not isinstance(obj, models.Model):
            return None

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


class InheritanceQuerySet(InheritanceQuerySetMixin, QuerySet):
    pass


class InheritanceManagerMixin(object):
    _queryset_class = InheritanceQuerySet

    def get_queryset(self):
        return self._queryset_class(self.model)

    def select_subclasses(self, *subclasses):
        return self.get_queryset().select_subclasses(*subclasses)

    def get_subclass(self, *args, **kwargs):
        return self.get_queryset().get_subclass(*args, **kwargs)


class InheritanceManager(InheritanceManagerMixin, models.Manager):
    pass


class QueryManagerMixin(object):

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
        qs = super(QueryManagerMixin, self).get_queryset().filter(self._q)
        if self._order_by is not None:
            return qs.order_by(*self._order_by)
        return qs


class QueryManager(QueryManagerMixin, models.Manager):
    pass


class SoftDeletableQuerySetMixin(object):
    """
    QuerySet for SoftDeletableModel. Instead of removing instance sets
    its ``is_removed`` field to True.
    """

    def delete(self):
        """
        Soft delete objects from queryset (set their ``is_removed``
        field to True)
        """
        self.update(is_removed=True)


class SoftDeletableQuerySet(SoftDeletableQuerySetMixin, QuerySet):
    pass


class SoftDeletableManagerMixin(object):
    """
    Manager that limits the queryset by default to show only not removed
    instances of model.
    """
    _queryset_class = SoftDeletableQuerySet

    def get_queryset(self):
        """
        Return queryset limited to not removed entries.
        """
        kwargs = {'model': self.model, 'using': self._db}
        if hasattr(self, '_hints'):
            kwargs['hints'] = self._hints

        return self._queryset_class(**kwargs).filter(is_removed=False)


class SoftDeletableManager(SoftDeletableManagerMixin, models.Manager):
    pass
