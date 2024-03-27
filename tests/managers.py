from __future__ import annotations

from model_utils.managers import (
    ModelT,
    QuerySet,
    SoftDeletableManager,
    SoftDeletableQuerySet,
)


class CustomSoftDeleteQuerySet(SoftDeletableQuerySet[ModelT]):
    def only_read(self) -> QuerySet[ModelT]:
        return self.filter(is_read=True)


class CustomSoftDeleteManager(SoftDeletableManager[ModelT]):
    _queryset_class = CustomSoftDeleteQuerySet

    def only_read(self) -> QuerySet[ModelT]:
        qs = self.get_queryset()
        assert isinstance(qs, self._queryset_class), qs
        return qs.only_read()
