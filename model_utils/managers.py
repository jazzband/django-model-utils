from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Generic, TypeVar, cast

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import OneToOneField, OneToOneRel
from django.db.models.sql.datastructures import Join

ModelT = TypeVar('ModelT', bound=models.Model, covariant=True)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Any

    from django.db.models.query import BaseIterable
    from django.db.models.query import ModelIterable as ModelIterableGeneric
    from django.db.models.query import QuerySet as QuerySetGeneric
    from django.db.models.sql.query import Query

    ModelIterable = ModelIterableGeneric[ModelT]
    QuerySet = QuerySetGeneric[ModelT]
else:
    from django.db.models.query import ModelIterable, QuerySet


class InheritanceIterable(ModelIterable):
    def __iter__(self) -> Iterator[ModelT]:
        queryset = self.queryset
        iter: Iterable[ModelT] = ModelIterable(queryset)
        if hasattr(queryset, 'subclasses'):
            extras = tuple(queryset.query.extra.keys())
            # sort the subclass names longest first,
            # so with 'a' and 'a__b' it goes as deep as possible
            subclasses = sorted(queryset.subclasses, key=len, reverse=True)
            for obj in iter:
                sub_obj = None
                for s in subclasses:
                    assert hasattr(queryset, '_get_sub_obj_recurse')
                    sub_obj = queryset._get_sub_obj_recurse(obj, s)
                    if sub_obj:
                        break
                if not sub_obj:
                    sub_obj = obj

                if hasattr(queryset, '_annotated'):
                    for k in queryset._annotated:
                        setattr(sub_obj, k, getattr(obj, k))

                for k in extras:
                    setattr(sub_obj, k, getattr(obj, k))

                yield sub_obj
        else:
            yield from iter


class InheritanceQuerySetMixin(Generic[ModelT]):

    # Defining an attribute using a generic type will trigger a bug in mypy:
    # https://github.com/python/mypy/issues/9031
    # model: type[ModelT]

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._iterable_class: type[BaseIterable] = InheritanceIterable

    def select_subclasses(self, *subclasses: str | type[models.Model]) -> InheritanceQuerySet[ModelT]:
        levels = None
        model: type[ModelT] = self.model  # type: ignore[attr-defined]
        calculated_subclasses = self._get_subclasses_recurse(model, levels=levels)
        # if none were passed in, we can just short circuit and select all
        if not subclasses:
            selected_subclasses = calculated_subclasses
        else:
            verified_subclasses: list[str] = []
            for subclass in subclasses:
                # special case for passing in the same model as the queryset
                # is bound against. Rather than raise an error later, we know
                # we can allow this through.
                if subclass is model:
                    continue

                if not isinstance(subclass, str):
                    subclass = self._get_ancestors_path(
                        subclass, levels=levels)

                if subclass in calculated_subclasses:
                    verified_subclasses.append(subclass)
                else:
                    raise ValueError(
                        '{!r} is not in the discovered subclasses, tried: {}'.format(
                            subclass, ', '.join(calculated_subclasses))
                    )
            selected_subclasses = verified_subclasses

        new_qs = cast('InheritanceQuerySet[ModelT]', self)
        if selected_subclasses:
            new_qs = new_qs.select_related(*selected_subclasses)
        new_qs.subclasses = selected_subclasses  # type: ignore[attr-defined]
        return new_qs

    def _chain(self, **kwargs: object) -> InheritanceQuerySet[ModelT]:
        update = {}
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                update[name] = getattr(self, name)

        # django-stubs doesn't include private API.
        chained = super()._chain(**kwargs)  # type: ignore[misc]
        chained.__dict__.update(update)
        return chained

    def _clone(self) -> InheritanceQuerySet[ModelT]:
        # django-stubs doesn't include private API.
        qs = super()._clone()  # type: ignore[misc]
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                setattr(qs, name, getattr(self, name))
        return qs

    def annotate(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
        qset = cast(QuerySet, super()).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset

    def _get_subclasses_recurse(
        self,
        model: type[models.Model],
        levels: int | None = None
    ) -> list[str]:
        """
        Given a Model class, find all related objects, exploring children
        recursively, returning a `list` of strings representing the
        relations for select_related
        """
        related_objects = [
            f for f in model._meta.get_fields()
            if isinstance(f, OneToOneRel)]

        rels = [
            rel for rel in related_objects
            if isinstance(rel.field, OneToOneField)
            and issubclass(rel.field.model, model)
            and model is not rel.field.model
            and rel.parent_link
        ]

        subclasses = []
        if levels:
            levels -= 1
        for rel in rels:
            if levels or levels is None:
                for subclass in self._get_subclasses_recurse(
                        rel.field.model, levels=levels):
                    accessor_name = rel.get_accessor_name()
                    assert accessor_name is not None
                    subclasses.append(accessor_name + LOOKUP_SEP + subclass)
            accessor_name = rel.get_accessor_name()
            assert accessor_name is not None
            subclasses.append(accessor_name)
        return subclasses

    def _get_ancestors_path(
        self,
        model: type[models.Model],
        levels: int | None = None
    ) -> str:
        """
        Serves as an opposite to _get_subclasses_recurse, instead walking from
        the Model class up the Model's ancestry and constructing the desired
        select_related string backwards.
        """
        ancestor: type[ModelT] = self.model  # type: ignore[attr-defined]
        if not issubclass(model, ancestor):
            raise ValueError(
                f"{model!r} is not a subclass of {ancestor!r}")

        ancestry: list[str] = []
        # should be a OneToOneField or None
        parent_link = model._meta.get_ancestor_link(ancestor)
        if levels:
            levels -= 1
        while parent_link is not None:
            related = parent_link.remote_field
            accessor_name = related.get_accessor_name()
            assert accessor_name is not None
            ancestry.insert(0, accessor_name)
            if levels or levels is None:
                parent_model = related.model
                parent_link = parent_model._meta.get_ancestor_link(ancestor)
            else:
                parent_link = None
        return LOOKUP_SEP.join(ancestry)

    def _get_sub_obj_recurse(self, obj: models.Model, s: str) -> ModelT | None:
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

    def get_subclass(self, *args: object, **kwargs: object) -> ModelT:
        return self.select_subclasses().get(*args, **kwargs)


class InheritanceQuerySet(InheritanceQuerySetMixin[ModelT], QuerySet[ModelT]):
    def instance_of(self, *models: type[ModelT]) -> InheritanceQuerySet[ModelT]:
        """
        Fetch only objects that are instances of the provided model(s).
        """
        # If we aren't already selecting the subclasses, we need
        # to in order to get this to work.

        # How can we tell if we are not selecting subclasses?

        # Is it safe to just apply .select_subclasses(*models)?

        # Due to https://code.djangoproject.com/ticket/16572, we
        # can't really do this for anything other than children (ie,
        # no grandchildren+).
        where_queries = []
        for model in models:
            where_queries.append('(' + ' AND '.join([
                '"{}"."{}" IS NOT NULL'.format(
                    model._meta.db_table,
                    field.column,
                ) for field in model._meta.parents.values()
            ]) + ')')

        return cast(
            'InheritanceQuerySet[ModelT]',
            self.select_subclasses(*models).extra(where=[' OR '.join(where_queries)])
        )


class InheritanceManagerMixin(Generic[ModelT]):
    _queryset_class = InheritanceQuerySet

    if TYPE_CHECKING:
        def filter(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
            ...

    def get_queryset(self) -> InheritanceQuerySet[ModelT]:
        model: type[ModelT] = self.model  # type: ignore[attr-defined]
        return self._queryset_class(model)

    def select_subclasses(
        self, *subclasses: str | type[models.Model]
    ) -> InheritanceQuerySet[ModelT]:
        return self.get_queryset().select_subclasses(*subclasses)

    def get_subclass(self, *args: object, **kwargs: object) -> ModelT:
        return self.get_queryset().get_subclass(*args, **kwargs)

    def instance_of(self, *models: type[ModelT]) -> QuerySet:
        return self.get_queryset().instance_of(*models)


class InheritanceManager(InheritanceManagerMixin[ModelT], models.Manager[ModelT]):
    pass


class QueryManagerMixin(Generic[ModelT]):

    def __init__(self, *args: models.Q, **kwargs: object):
        if args:
            self._q = args[0]
        else:
            self._q = models.Q(**kwargs)
        self._order_by: tuple[Any, ...] | None = None
        super().__init__()

    # Using a generic type as the return type will trigger a bug in mypy:
    # https://github.com/python/mypy/issues/9031
    # def order_by(self, *args: Any) -> QueryManager[ModelT]:
    def order_by(self, *args: Any) -> Any:
        self._order_by = args
        return cast('QueryManager[ModelT]', self)

    def get_queryset(self) -> QuerySet[ModelT]:
        qs = super().get_queryset()  # type: ignore[misc]
        qs = qs.filter(self._q)
        if self._order_by is not None:
            return qs.order_by(*self._order_by)
        return qs


class QueryManager(QueryManagerMixin[ModelT], models.Manager):
    pass


class SoftDeletableQuerySetMixin(Generic[ModelT]):
    """
f    QuerySet for SoftDeletableModel. Instead of removing instance sets
    its ``is_removed`` field to True.
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Soft delete objects from queryset (set their ``is_removed``
        field to True)
        """
        cast(QuerySet, self).update(is_removed=True)
        return (0, {})  # no objects were actually deleted


class SoftDeletableQuerySet(SoftDeletableQuerySetMixin[ModelT], QuerySet):
    pass


class SoftDeletableManagerMixin(Generic[ModelT]):
    """
    Manager that limits the queryset by default to show only not removed
    instances of model.
    """
    _queryset_class = SoftDeletableQuerySet

    _db: str | None

    def __init__(
        self,
        *args: object,
        _emit_deprecation_warnings: bool = False,
        **kwargs: object
    ):
        self.emit_deprecation_warnings = _emit_deprecation_warnings
        super().__init__(*args, **kwargs)

    def get_queryset(self) -> SoftDeletableQuerySet[ModelT]:
        """
        Return queryset limited to not removed entries.
        """

        model: type[ModelT] = self.model  # type: ignore[attr-defined]

        if self.emit_deprecation_warnings:
            warning_message = (
                "{0}.objects model manager will include soft-deleted objects in an "
                "upcoming release; please use {0}.available_objects to continue "
                "excluding soft-deleted objects. See "
                "https://django-model-utils.readthedocs.io/en/stable/models.html"
                "#softdeletablemodel for more information."
            ).format(model.__class__.__name__)
            warnings.warn(warning_message, DeprecationWarning)

        return self._queryset_class(
            model=model,
            using=self._db,
            **({'hints': self._hints} if hasattr(self, '_hints') else {})
        ).filter(is_removed=False)


class SoftDeletableManager(SoftDeletableManagerMixin[ModelT], models.Manager):
    pass


class JoinQueryset(models.QuerySet):

    def get_quoted_query(self, query: Query) -> str:
        query_str, params = query.sql_with_params()

        # Put additional quotes around string.
        params = tuple(
            f'\'{p}\''
            if isinstance(p, str) else p
            for p in params
        )

        return query_str % params

    def join(self, qs: QuerySet | None = None) -> QuerySet:
        '''
        Join one queryset together with another using a temporary table. If
        no queryset is used, it will use the current queryset and join that
        to itself.

        `Join` either uses the current queryset and effectively does a self-join to
        create a new limited queryset OR it uses a queryset given by the user.

        The model of a given queryset needs to contain a valid foreign key to
        the current queryset to perform a join. A new queryset is then created.
        '''
        to_field = 'id'

        if qs:
            fks = [
                fk for fk in qs.model._meta.fields
                if getattr(fk, 'related_model', None) == self.model
            ]
            fk = fks[0] if fks else None
            model_set = f'{self.model.__name__.lower()}_set'
            key = fk or getattr(qs.model, model_set, None)

            if not key:
                raise ValueError('QuerySet is not related to current model')

            try:
                fk_column = key.column
            except AttributeError:
                fk_column = 'id'
                to_field = key.field.column

            qs = qs.only(fk_column)
            # if we give a qs we need to keep the model qs to not lose anything
            new_qs = self
        else:
            fk_column = 'id'
            qs = self.only(fk_column)
            new_qs = self.model.objects.all()

        TABLE_NAME = 'temp_stuff'
        query = self.get_quoted_query(qs.query)
        sql = '''
            DROP TABLE IF EXISTS {table_name};
            DROP INDEX IF EXISTS {table_name}_id;
            CREATE TEMPORARY TABLE {table_name} AS {query};
            CREATE INDEX {table_name}_{fk_column} ON {table_name} ({fk_column});
        '''.format(table_name=TABLE_NAME, fk_column=fk_column, query=str(query))

        with connection.cursor() as cursor:
            cursor.execute(sql)

        class TempModel(models.Model):
            temp_key = models.ForeignKey(
                self.model,
                on_delete=models.DO_NOTHING,
                db_column=fk_column,
                to_field=to_field
            )

            class Meta:
                managed = False
                db_table = TABLE_NAME

        conn = Join(
            table_name=TempModel._meta.db_table,
            parent_alias=new_qs.query.get_initial_alias(),
            table_alias=None,
            join_type='INNER JOIN',
            join_field=self.model.tempmodel_set.rel,
            nullable=False
        )
        new_qs.query.join(conn, reuse=None)
        return new_qs


class JoinManagerMixin(Generic[ModelT]):
    """
    Manager that adds a method join. This method allows you to join two
    querysets together.
    """
    _queryset_class = JoinQueryset

    _db: str | None

    def get_queryset(self) -> JoinQueryset:
        model: type[ModelT] = self.model  # type: ignore[attr-defined]
        return self._queryset_class(model=model, using=self._db)


class JoinManager(JoinManagerMixin[ModelT], models.Manager):
    pass
