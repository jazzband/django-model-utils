import sys

from django.db import IntegrityError, models, transaction
from django.db.models.fields.related import OneToOneField
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist


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
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                kwargs[name] = getattr(self, name)
        return super(InheritanceQuerySet, self)._clone(klass, setup, **kwargs)

    def annotate(self, *args, **kwargs):
        qset = super(InheritanceQuerySet, self).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + kwargs.keys()
        return qset

    def iterator(self):
        iter = super(InheritanceQuerySet, self).iterator()
        if getattr(self, 'subclasses', False):
            for obj in iter:
                for s in self.subclasses:
                    try:
                        sub_obj = getattr(obj, s)
                    except ObjectDoesNotExist:
                        sub_obj = None
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
        if self._queryset_cls is not None:
            kargs = {'model': self.model}
            if hasattr(self, '_db'):
                kargs['using'] = self._db
            return self._queryset_cls(**kargs)
        return super(PassThroughManager, self).get_query_set()

    @classmethod
    def for_queryset_class(cls, queryset_cls):
        return create_pass_through_manager_for_queryset_class(cls, queryset_cls)


def create_pass_through_manager_for_queryset_class(base, queryset_cls):
    class _PassThroughManager(base):
        def __init__(self):
            return super(_PassThroughManager, self).__init__()

        def get_query_set(self):
            kwargs = {}
            if hasattr(self, "_db"):
                kwargs["using"] = self._db
            return queryset_cls(self.model, **kwargs)

        def __reduce__(self):
            return (
                unpickle_pass_through_manager_for_queryset_class,
                (base, queryset_cls),
                self.__dict__,
                )

    return _PassThroughManager


def unpickle_pass_through_manager_for_queryset_class(base, queryset_cls):
    cls = create_pass_through_manager_for_queryset_class(base, queryset_cls)
    return cls.__new__(cls)


class UpdateOrCreateMixin(object):
    def update_or_create(self, **kwargs):
        """
        Looks up an object with the given kwargs, creating one if necessary.
        If the object already exists, then its fields are updated with the
        values passed in the defaults dictionary.
        Returns a tuple of (object, created), where created is a boolean
        specifying whether an object was created.

        See https://code.djangoproject.com/ticket/3182
        """
        assert kwargs, \
            'update_or_create() must be passed at least one keyword argument'
        defaults = kwargs.pop('defaults', {})
        lookup = kwargs.copy()
        for f in self.model._meta.fields:
            if f.attname in lookup:
                lookup[f.name] = lookup.pop(f.attname)
        self._for_write = True
        sid = transaction.savepoint(using=self.db)
        try:
            obj = self.get(**lookup)
            create = False
        except self.model.DoesNotExist:
            params = dict([(k, v) for k, v in kwargs.items() if '__' not in k])
            obj = self.model(**params)
            create = True
        for attname, value in defaults.items():
            setattr(obj, attname, value)
        try:
            obj.save(force_insert=create, using=self.db)
            transaction.savepoint_commit(sid, using=self.db)
            return obj, create
        except IntegrityError:
            transaction.savepoint_rollback(sid, using=self.db)
            exc_info = sys.exc_info()
            raise exc_info[1], None, exc_info[2]
