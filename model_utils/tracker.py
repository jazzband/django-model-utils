from __future__ import unicode_literals

from copy import deepcopy

import django
from django.core.exceptions import FieldError
from django.db import models
from django.db.models.fields.files import FileDescriptor
from django.db.models.query_utils import DeferredAttribute


class DescriptorMixin(object):
    tracker_instance = None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        was_deferred = False
        field_name = self._get_field_name()
        if field_name in instance._deferred_fields:
            instance._deferred_fields.remove(field_name)
            was_deferred = True
        value = super(DescriptorMixin, self).__get__(instance, owner)
        if was_deferred:
            self.tracker_instance.saved_data[field_name] = deepcopy(value)
        return value

    def _get_field_name(self):
        return self.field_name


class DescriptorWrapper(object):

    def __init__(self, field_name, descriptor, tracker_attname):
        self.field_name = field_name
        self.descriptor = descriptor
        self.tracker_attname = tracker_attname

    def __get__(self, instance, owner):
        if instance is None:
            return self
        was_deferred = self.field_name in instance.get_deferred_fields()
        try:
            value = self.descriptor.__get__(instance, owner)
        except AttributeError:
            value = self.descriptor
        if was_deferred:
            tracker_instance = getattr(instance, self.tracker_attname)
            tracker_instance.saved_data[self.field_name] = deepcopy(value)
        return value

    def __set__(self, instance, value):
        initialized = hasattr(instance, '_instance_intialized')
        was_deferred = self.field_name in instance.get_deferred_fields()

        # Sentinel attribute to detect whether we are already trying to
        # set the attribute higher up the stack. This prevents infinite
        # recursion when retrieving deferred values from the database.
        recursion_sentinel_attname = '_setting_' + self.field_name
        already_setting = hasattr(instance, recursion_sentinel_attname)

        if initialized and was_deferred and not already_setting:
            setattr(instance, recursion_sentinel_attname, True)
            try:
                # Retrieve the value to set the saved_data value.
                # This will undefer the field
                getattr(instance, self.field_name)
            finally:
                instance.__dict__.pop(recursion_sentinel_attname, None)
        if hasattr(self.descriptor, '__set__'):
            self.descriptor.__set__(instance, value)
        else:
            instance.__dict__[self.field_name] = value

    @staticmethod
    def cls_for_descriptor(descriptor):
        if hasattr(descriptor, '__delete__'):
            return FullDescriptorWrapper
        else:
            return DescriptorWrapper


class FullDescriptorWrapper(DescriptorWrapper):
    """
    Wrapper for descriptors with all three descriptor methods.
    """
    def __delete__(self, obj):
        self.descriptor.__delete__(obj)


class FieldInstanceTracker(object):
    def __init__(self, instance, fields, field_map):
        self.instance = instance
        self.fields = fields
        self.field_map = field_map
        if django.VERSION < (1, 10):
            self.init_deferred_fields()

    @property
    def deferred_fields(self):
        return self.instance._deferred_fields if django.VERSION < (1, 10) else self.instance.get_deferred_fields()

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
            deferred_fields = self.deferred_fields
            if deferred_fields:
                fields = [
                    field for field in self.fields
                    if field not in deferred_fields
                ]
            else:
                fields = self.fields

        return dict((f, self.get_field_value(f)) for f in fields)

    def has_changed(self, field):
        """Returns ``True`` if field has changed from currently saved value"""
        if field in self.fields:
            # deferred fields haven't changed
            if field in self.deferred_fields and field not in self.instance.__dict__:
                return False
            return self.previous(field) != self.get_field_value(field)
        else:
            raise FieldError('field "%s" not tracked' % field)

    def previous(self, field):
        """Returns currently saved value of given field"""

        # handle deferred fields that have not yet been loaded from the database
        if self.instance.pk and field in self.deferred_fields and field not in self.saved_data:

            # if the field has not been assigned locally, simply fetch and un-defer the value
            if field not in self.instance.__dict__:
                self.get_field_value(field)

            # if the field has been assigned locally, store the local value, fetch the database value,
            # store database value to saved_data, and restore the local value
            else:
                current_value = self.get_field_value(field)
                self.instance.refresh_from_db(fields=[field])
                self.saved_data[field] = deepcopy(self.get_field_value(field))
                setattr(self.instance, self.field_map[field], current_value)

        return self.saved_data.get(field)

    def changed(self):
        """Returns dict of fields that changed since save (with old values)"""
        return dict(
            (field, self.previous(field))
            for field in self.fields
            if self.has_changed(field)
        )

    def init_deferred_fields(self):
        self.instance._deferred_fields = set()
        if hasattr(self.instance, '_deferred') and not self.instance._deferred:
            return

        class DeferredAttributeTracker(DescriptorMixin, DeferredAttribute):
            tracker_instance = self

        class FileDescriptorTracker(DescriptorMixin, FileDescriptor):
            tracker_instance = self

            def _get_field_name(self):
                return self.field.name

        self.instance._deferred_fields = self.instance.get_deferred_fields()
        for field in self.instance._deferred_fields:
            field_obj = self.instance.__class__.__dict__.get(field)
            if isinstance(field_obj, FileDescriptor):
                field_tracker = FileDescriptorTracker(field_obj.field)
                setattr(self.instance.__class__, field, field_tracker)
            else:
                field_tracker = DeferredAttributeTracker(field, type(self.instance))
                setattr(self.instance.__class__, field, field_tracker)


class FieldTracker(object):

    tracker_class = FieldInstanceTracker

    def __init__(self, fields=None):
        self.fields = fields

    def get_field_map(self, cls):
        """Returns dict mapping fields names to model attribute names"""
        field_map = dict((field, field) for field in self.fields)
        all_fields = dict((f.name, f.attname) for f in cls._meta.fields)
        field_map.update(**dict((k, v) for (k, v) in all_fields.items()
                                if k in field_map))
        return field_map

    def contribute_to_class(self, cls, name):
        self.name = name
        self.attname = '_%s' % name
        models.signals.class_prepared.connect(self.finalize_class, sender=cls)

    def finalize_class(self, sender, **kwargs):
        if self.fields is None:
            self.fields = (field.attname for field in sender._meta.fields)
        self.fields = set(self.fields)
        if django.VERSION >= (1, 10):
            for field_name in self.fields:
                descriptor = getattr(sender, field_name)
                wrapper_cls = DescriptorWrapper.cls_for_descriptor(descriptor)
                wrapped_descriptor = wrapper_cls(field_name, descriptor, self.attname)
                setattr(sender, field_name, wrapped_descriptor)
        self.field_map = self.get_field_map(sender)
        models.signals.post_init.connect(self.initialize_tracker)
        self.model_class = sender
        setattr(sender, self.name, self)
        self.patch_save(sender)

    def initialize_tracker(self, sender, instance, **kwargs):
        if not isinstance(instance, self.model_class):
            return  # Only init instances of given model (including children)
        tracker = self.tracker_class(instance, self.fields, self.field_map)
        setattr(instance, self.attname, tracker)
        tracker.set_saved_fields()
        instance._instance_intialized = True

    def patch_save(self, model):
        original_save = model.save

        def save(instance, *args, **kwargs):
            ret = original_save(instance, *args, **kwargs)
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

        model.save = save

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
