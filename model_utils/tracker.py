from __future__ import unicode_literals

from copy import deepcopy

from django.db import models
from django.core.exceptions import FieldError
from django.db.models.query_utils import DeferredAttribute


class FieldInstanceTracker(object):
    def __init__(self, instance, fields, field_map):
        self.instance = instance
        self.fields = fields
        self.field_map = field_map
        self.init_deferred_fields()

    def get_field_value(self, field):
        return getattr(self.instance, self.field_map[field])

    def set_saved_fields(self, fields=None):
        if not self.instance.pk:
            self.saved_data = {}
        elif fields is None:
            self.saved_data = self.current()
        else:
            self.saved_data.update(**self.current(fields=fields))

        # preventing mutable fields side effects
        for field, field_value in self.saved_data.items():
            self.saved_data[field] = deepcopy(field_value)

    def current(self, fields=None):
        """Returns dict of current values for all tracked fields"""
        if fields is None:
            if self.deferred_fields:
                fields = [
                    field for field in self.fields
                    if field not in self.deferred_fields
                ]
            else:
                fields = self.fields

        return dict((f, self.get_field_value(f)) for f in fields)

    def has_changed(self, field):
        """Returns ``True`` if field has changed from currently saved value"""
        if field in self.fields:
            return self.previous(field) != self.get_field_value(field)
        else:
            raise FieldError('field "%s" not tracked' % field)

    def previous(self, field):
        """Returns currently saved value of given field"""
        return self.saved_data.get(field)

    def changed(self):
        """Returns dict of fields that changed since save (with old values)"""
        return dict(
            (field, self.previous(field))
            for field in self.fields
            if self.has_changed(field)
        )

    def init_deferred_fields(self):
        self.deferred_fields = []
        if not self.instance._deferred:
            return

        class DeferredAttributeTracker(DeferredAttribute):
            def __get__(field, instance, owner):
                data = instance.__dict__
                if data.get(field.field_name, field) is field:
                    self.deferred_fields.remove(field.field_name)
                    value = super(DeferredAttributeTracker, field).__get__(
                        instance, owner)
                    self.saved_data[field.field_name] = deepcopy(value)
                return data[field.field_name]

        for field in self.fields:
            field_obj = self.instance.__class__.__dict__.get(field)
            if isinstance(field_obj, DeferredAttribute):
                self.deferred_fields.append(field)

                # Django 1.4
                model = None
                if hasattr(field_obj, 'model_ref'):
                    model = field_obj.model_ref()

                field_tracker = DeferredAttributeTracker(
                    field_obj.field_name, model)
                setattr(self.instance.__class__, field, field_tracker)


class FieldTracker(object):

    tracker_class = FieldInstanceTracker

    def __init__(self, fields=None):
        self.fields = fields

    def get_field_map(self, cls):
        """Returns dict mapping fields names to model attribute names"""
        field_map = dict((field, field) for field in self.fields)
        all_fields = dict((f.name, f.attname) for f in cls._meta.local_fields)
        field_map.update(**dict((k, v) for (k, v) in all_fields.items()
                                if k in field_map))
        return field_map

    def contribute_to_class(self, cls, name):
        self.name = name
        self.attname = '_%s' % name
        models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def finalize_class(self, sender, **kwargs):
        if self.fields is None:
            self.fields = (field.attname for field in sender._meta.local_fields)
        self.fields = set(self.fields)
        self.field_map = self.get_field_map(sender)
        models.signals.post_init.connect(self.initialize_tracker)
        self.model_class = sender
        setattr(sender, self.name, self)

    def initialize_tracker(self, sender, instance, **kwargs):
        if not isinstance(instance, self.model_class):
            return  # Only init instances of given model (including children)
        tracker = self.tracker_class(instance, self.fields, self.field_map)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()
        self.patch_save(instance)

    def patch_save(self, instance):
        original_save = instance.save
        def save(**kwargs):
            ret = original_save(**kwargs)
            update_fields = kwargs.get('update_fields')
            if not update_fields and update_fields is not None:  # () or []
                fields = update_fields
            elif update_fields is None:
                fields = None
            else:
                fields = (
                    field for field in update_fields if
                    field in self.fields
                )
            getattr(instance, self.attname).set_saved_fields(
                fields=fields
            )
            return ret
        instance.save = save

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return getattr(instance, self.attname)


class ModelInstanceTracker(FieldInstanceTracker):

    def has_changed(self, field):
        """Returns ``True`` if field has changed from currently saved value"""
        if not self.instance.pk:
            return True
        elif field in self.saved_data:
            return self.previous(field) != self.get_field_value(field)
        else:
            raise FieldError('field "%s" not tracked' % field)

    def changed(self):
        """Returns dict of fields that changed since save (with old values)"""
        if not self.instance.pk:
            return {}
        saved = self.saved_data.items()
        current = self.current()
        return dict((k, v) for k, v in saved if v != current[k])


class ModelTracker(FieldTracker):
    tracker_class = ModelInstanceTracker

    def get_field_map(self, cls):
        return dict((field, field) for field in self.fields)
