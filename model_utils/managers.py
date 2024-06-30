from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Generic, Sequence, TypeVar, cast, overload

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import OneToOneField, OneToOneRel
from django.db.models.query import ModelIterable, QuerySet
from django.db.models.sql.datastructures import Join

ModelT = TypeVar('ModelT', bound=models.Model, covariant=True)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from django.db.models.query import BaseIterable


def _iter_inheritance_queryset(queryset: QuerySet[ModelT]) -> Iterator[ModelT]:
    iter: ModelIterable[ModelT] = ModelIterable(queryset)
    if hasattr(queryset, 'subclasses'):
        assert hasattr(queryset, '_get_sub_obj_recurse')
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

            if hasattr(queryset, '_annotated'):
                for k in queryset._annotated:
                    setattr(sub_obj, k, getattr(obj, k))

            for k in extras:
                setattr(sub_obj, k, getattr(obj, k))

            yield sub_obj
    else:
        yield from iter


if TYPE_CHECKING:
    class InheritanceIterable(ModelIterable[ModelT]):
        queryset: QuerySet[ModelT]

        def __init__(self, queryset: QuerySet[ModelT], *args: Any, **kwargs: Any):
            ...

        def __iter__(self) -> Iterator[ModelT]:
            ...

else:
    class InheritanceIterable(ModelIterable):
        def __iter__(self):
            return _iter_inheritance_queryset(self.queryset)


class InheritanceQuerySetMixin(Generic[ModelT]):

    model: type[ModelT]
    subclasses: Sequence[str]

    def __init__(self, *args: object, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._iterable_class: type[BaseIterable[ModelT]] = InheritanceIterable

    def select_subclasses(self, *subclasses: str | type[models.Model]) -> InheritanceQuerySet[ModelT]:
        model: type[ModelT] = self.model
        calculated_subclasses = self._get_subclasses_recurse(model)
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
                    subclass = self._get_ancestors_path(subclass)

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
        new_qs.subclasses = selected_subclasses
        return new_qs

    def _chain(self, **kwargs: object) -> InheritanceQuerySet[ModelT]:
        update = {}
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                update[name] = getattr(self, name)

        # django-stubs doesn't include this private API.
        chained = super()._chain(**kwargs)  # type: ignore[misc]
        chained.__dict__.update(update)
        return chained

    def _clone(self) -> InheritanceQuerySet[ModelT]:
        # django-stubs doesn't include this private API.
        qs = super()._clone()  # type: ignore[misc]
        for name in ['subclasses', '_annotated']:
            if hasattr(self, name):
                setattr(qs, name, getattr(self, name))
        return qs

    def annotate(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
        qset = cast(QuerySet[ModelT], super()).annotate(*args, **kwargs)
        qset._annotated = [a.default_alias for a in args] + list(kwargs.keys())
        return qset

    def _get_subclasses_recurse(self, model: type[models.Model]) -> list[str]:
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

        for rel in rels:
            for subclass in self._get_subclasses_recurse(rel.field.model):
                subclasses.append(rel.get_accessor_name() + LOOKUP_SEP + subclass)
            subclasses.append(rel.get_accessor_name())
        return subclasses

    def _get_ancestors_path(self, model: type[models.Model]) -> str:
        """
        Serves as an opposite to _get_subclasses_recurse, instead walking from
        the Model class up the Model's ancestry and constructing the desired
        select_related string backwards.
        """
        if not issubclass(model, self.model):
            raise ValueError(
                f"{model!r} is not a subclass of {self.model!r}")

        ancestry: list[str] = []
        # should be a OneToOneField or None
        parent_link = model._meta.get_ancestor_link(self.model)

        while parent_link is not None:
            related = parent_link.remote_field
            ancestry.insert(0, related.get_accessor_name())

            parent_model = related.model
            parent_link = parent_model._meta.get_ancestor_link(self.model)

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


# Defining the 'model' attribute using a generic type triggers a bug in mypy:
# https://github.com/python/mypy/issues/9031
class InheritanceQuerySet(InheritanceQuerySetMixin[ModelT], QuerySet[ModelT]):  # type: ignore[misc]
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
        from collections.abc import Sequence

        def none(self) -> InheritanceQuerySet[ModelT]:
            ...

        def all(self) -> InheritanceQuerySet[ModelT]:
            ...

        def filter(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def exclude(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def complex_filter(self, filter_obj: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def union(self, *other_qs: Any, all: bool = ...) -> InheritanceQuerySet[ModelT]:
            ...

        def intersection(self, *other_qs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def difference(self, *other_qs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def select_for_update(
            self, nowait: bool = ..., skip_locked: bool = ..., of: Sequence[str] = ..., no_key: bool = ...
        ) -> InheritanceQuerySet[ModelT]:
            ...

        def select_related(self, *fields: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def prefetch_related(self, *lookups: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def annotate(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def alias(self, *args: Any, **kwargs: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def order_by(self, *field_names: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def distinct(self, *field_names: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def extra(
            self,
            select: dict[str, Any] | None = ...,
            where: list[str] | None = ...,
            params: list[Any] | None = ...,
            tables: list[str] | None = ...,
            order_by: Sequence[str] | None = ...,
            select_params: Sequence[Any] | None = ...,
        ) -> InheritanceQuerySet[Any]:
            ...

        def reverse(self) -> InheritanceQuerySet[ModelT]:
            ...

        def defer(self, *fields: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def only(self, *fields: Any) -> InheritanceQuerySet[ModelT]:
            ...

        def using(self, alias: str | None) -> InheritanceQuerySet[ModelT]:
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

    def instance_of(self, *models: type[ModelT]) -> InheritanceQuerySet[ModelT]:
        return self.get_queryset().instance_of(*models)


class InheritanceManager(InheritanceManagerMixin[ModelT], models.Manager[ModelT]):
    pass


class QueryManagerMixin(Generic[ModelT]):

    @overload
    def __init__(self, *args: models.Q):
        ...

    @overload
    def __init__(self, **kwargs: object):
        ...

    def __init__(self, *args: models.Q, **kwargs: object):
        if args:
            self._q = args[0]
        else:
            self._q = models.Q(**kwargs)
        self._order_by: tuple[Any, ...] | None = None
        super().__init__()

    def order_by(self, *args: Any) -> QueryManager[ModelT]:
        self._order_by = args
        return cast('QueryManager[ModelT]', self)

    def get_queryset(self) -> QuerySet[ModelT]:
        qs = super().get_queryset()  # type: ignore[misc]
        qs = qs.filter(self._q)
        if self._order_by is not None:
            return qs.order_by(*self._order_by)
        return qs


class QueryManager(QueryManagerMixin[ModelT], models.Manager[ModelT]):  # type: ignore[misc]
    pass


class SoftDeletableQuerySetMixin(Generic[ModelT]):
    """
    QuerySet for SoftDeletableModel. Instead of removing instance sets
    its ``is_removed`` field to True.
    """

    def delete(self) -> tuple[int, dict[str, int]]:
        """
        Soft delete objects from queryset (set their ``is_removed``
        field to True)
        """
        model: type[ModelT] = self.model  # type: ignore[attr-defined]
        number_of_deleted_objects = cast(QuerySet[ModelT], self).update(is_removed=True)
        return number_of_deleted_objects, {model._meta.label: number_of_deleted_objects}


class SoftDeletableQuerySet(SoftDeletableQuerySetMixin[ModelT], QuerySet[ModelT]):
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


class SoftDeletableManager(SoftDeletableManagerMixin[ModelT], models.Manager[ModelT]):
    pass


class JoinQueryset(models.QuerySet[Any]):

    def join(self, qs: QuerySet[Any] | None = None) -> QuerySet[Any]:
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
            new_qs = self.model._default_manager.all()

        TABLE_NAME = 'temp_stuff'
        query, params = qs.query.sql_with_params()
        sql = '''
            DROP TABLE IF EXISTS {table_name};
            DROP INDEX IF EXISTS {table_name}_id;
            CREATE TEMPORARY TABLE {table_name} AS {query};
            CREATE INDEX {table_name}_{fk_column} ON {table_name} ({fk_column});
        '''.format(table_name=TABLE_NAME, fk_column=fk_column, query=str(query))

        with connection.cursor() as cursor:
            cursor.execute(sql, params)

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


if not TYPE_CHECKING:
    # Hide deprecated API during type checking, to encourage switch to
    # 'JoinQueryset.as_manager()', which is supported by the mypy plugin
    # of django-stubs.

    class JoinManagerMixin:
        """
        Manager that adds a method join. This method allows you to join two
        querysets together.
        """

        def get_queryset(self):
            warnings.warn(
                "JoinManager and JoinManagerMixin are deprecated. "
                "Please use 'JoinQueryset.as_manager()' instead.",
                DeprecationWarning
            )
            return self._queryset_class(model=self.model, using=self._db)

    class JoinManager(JoinManagerMixin):
        pass
