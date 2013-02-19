from django.db import models
from django.core.exceptions import FieldError


class ModelTracker(object):
    def __init__(self, fields=None):
        self.fields = fields

    def contribute_to_class(self, cls, name):
        self.name = name
        models.signals.class_prepared.connect(self.finalize, sender=cls)

    def finalize(self, sender, **kwargs):
        descriptor = ModelTrackerDescriptor(sender, self.name, self.fields)
        setattr(sender, self.name, descriptor)


class ModelTrackerDescriptor(object):
    def __init__(self, cls, name, fields):
        self.attname = '_%s' % name
        self.fields = fields
        if self.fields is None:
            self.fields = [field.attname for field in cls._meta.local_fields]
        models.signals.post_init.connect(self.initialize, sender=cls)

    def initialize(self, sender, instance, **kwargs):
        tracker = ModelInstanceTracker(instance, self.fields)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()
        self.patch_save(instance)

    def patch_save(self, instance):
        original_save = instance.save
        def save(**kwargs):
            ret = original_save()
            getattr(instance, self.attname).set_saved_fields()
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

    def set_saved_fields(self):
        self.saved_data = self.current_fields()

    def current_fields(self):
        return (dict((f, getattr(self.instance, f)) for f in self.fields)
                if self.instance.pk else {})

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
        current = self.current_fields()
        return dict((k, v) for k, v in saved if v != current[k])
