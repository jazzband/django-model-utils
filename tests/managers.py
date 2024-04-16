from model_utils.managers import SoftDeletableQuerySet


class CustomSoftDeleteQuerySet(SoftDeletableQuerySet):
    def only_read(self):
        return self.filter(is_read=True)
