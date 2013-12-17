class DenormalizeOnSaveMixin(object):
    """
    Adjusts a model's save method to denormalize data where it can

    This works by going through all related objects and calling its
    ``denormalize`` manager method.  Each of those methods should take
    one argument -- the model that's being saved.
    """
    def save(self, denormalize=True, *args, **kwargs):
        obj = super(DenormalizeOnSaveMixin, self).save(*args, **kwargs)
        # TODO: Abstract into a general library
        if denormalize:
            for a in self._meta.get_all_related_objects():
                if hasattr(a.model.objects, 'denormalize'):
                    a.model.objects.denormalize(self)
        return obj
