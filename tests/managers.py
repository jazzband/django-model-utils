from __future__ import unicode_literals, absolute_import

from model_utils.managers import SoftDeletableQuerySet, SoftDeletableManager


class CustomSoftDeleteQuerySet(SoftDeletableQuerySet):
    def only_read(self):
        return self.filter(is_read=True)


class CustomSoftDeleteManager(SoftDeletableManager):
    _queryset_class = CustomSoftDeleteQuerySet

    def only_read(self):
        return self.get_queryset().only_read()
