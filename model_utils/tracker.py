from django.db import models
from django.core.exceptions import FieldError


class ModelTracker(object):
    def __init__(self, fields=None):
        self.fields = fields

    def contribute_to_class(self, cls, name):
        self.name = name
        self.attname = '_%s' % name
        models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def finalize_class(self, sender, **kwargs):
        if self.fields is None:
            self.fields = [field.attname for field in sender._meta.local_fields]
        models.signals.post_init.connect(self.initialize_tracker, sender=sender)
        setattr(sender, self.name, self)

    def initialize_tracker(self, sender, instance, **kwargs):
        tracker = ModelInstanceTracker(instance, self.fields)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()
        self.patch_save(instance)

    def patch_save(self, instance):
        original_save = instance.save
        def save(**kwargs):
            ret = original_save()
            getattr(instance, self.attname).set_saved_fields(
                fields=kwargs.get('update_fields'))
            return ret
        instance.save = save

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return getattr(instance, self.attname)


class ModelInstanceTracker(object):
    def __init__(self, instance, fields):
        self.instance = instance
        self.fields = fields

    def set_saved_fields(self, fields=None):
        if not self.instance.pk:
            self.saved_data = {}
        elif fields is None:
            self.saved_data = self.current()
        else:
            self.saved_data.update(**self.current(fields=fields))

    def current(self, fields=None):
        if fields is None:
            fields = self.fields
        return dict((f, getattr(self.instance, f)) for f in fields)

    def has_changed(self, field):
        """Returns ``True`` if field has changed from currently saved value"""
        if not self.instance.pk:
            return True
        elif field in self.saved_data:
            return self.saved_data.get(field) != getattr(self.instance, field)
        else:
            raise FieldError('field "%s" not tracked' % field)

    def previous(self, field):
        """Return currently saved value of given field"""
        return self.saved_data.get(field)

    def changed(self):
        """Returns dict of fields that changed since save (with old values)"""
        if not self.instance.pk:
            return {}
        saved = self.saved_data.iteritems()
        current = self.current()
        return dict((k, v) for k, v in saved if v != current[k])
