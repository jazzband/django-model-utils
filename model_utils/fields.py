from datetime import datetime

from django.db import models
from django.conf import settings

from model_utils import Choices

class AutoCreatedField(models.DateTimeField):
    """
    A DateTimeField that automatically populates itself at
    object creation.

    By default, sets editable=False, default=datetime.now.

    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', datetime.now)
        super(AutoCreatedField, self).__init__(*args, **kwargs)


class AutoLastModifiedField(AutoCreatedField):
    """
    A DateTimeField that updates itself on each save() of the model.

    By default, sets editable=False and default=datetime.now.

    """
    def pre_save(self, model_instance, add):
        value = datetime.now()
        setattr(model_instance, self.attname, value)
        return value


class StatusField(models.CharField):
    """
    A CharField that looks for a ``STATUS`` class-attribute and
    automatically uses that as ``choices``. The first option in
    ``STATUS`` is set as the default.

    Also has a default max_length so you don't have to worry about
    setting that.

    Also features a ``no_check_for_status`` argument to make sure
    South can handle this field when it freezes a model.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 100)
        self.check_for_status = not kwargs.pop('no_check_for_status', False)
        super(StatusField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        if not cls._meta.abstract and self.check_for_status:
            assert hasattr(cls, 'STATUS'), \
                "To use StatusField, the model '%s' must have a STATUS choices class attribute." \
                % cls.__name__
            setattr(self, '_choices', cls.STATUS)
            setattr(self, 'default', tuple(cls.STATUS)[0][0]) # sets first as default
        super(StatusField, self).contribute_to_class(cls, name)


class MonitorField(models.DateTimeField):
    """
    A DateTimeField that monitors another field on the same model and
    sets itself to the current date/time whenever the monitored field
    changes.

    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', datetime.now)
        monitor = kwargs.pop('monitor', None)
        if not monitor:
            raise TypeError(
                '%s requires a "monitor" argument' % self.__class__.__name__)
        self.monitor = monitor
        super(MonitorField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        self.monitor_attname = '_monitor_%s' % name
        models.signals.post_init.connect(self._save_initial, sender=cls)
        super(MonitorField, self).contribute_to_class(cls, name)

    def get_monitored_value(self, instance):
        return getattr(instance, self.monitor)

    def _save_initial(self, sender, instance, **kwargs):
        setattr(instance, self.monitor_attname,
                self.get_monitored_value(instance))

    def pre_save(self, model_instance, add):
        value = datetime.now()
        previous = getattr(model_instance, self.monitor_attname, None)
        current = self.get_monitored_value(model_instance)
        if previous != current:
            setattr(model_instance, self.attname, value)
            self._save_initial(model_instance.__class__, model_instance)
        return super(MonitorField, self).pre_save(model_instance, add)


SPLIT_MARKER = getattr(settings, 'SPLIT_MARKER', '<!-- split -->')

# the number of paragraphs after which to split if no marker
SPLIT_DEFAULT_PARAGRAPHS = getattr(settings, 'SPLIT_DEFAULT_PARAGRAPHS', 2)

_excerpt_field_name = lambda name: '_%s_excerpt' % name

def get_excerpt(content):
    excerpt = []
    default_excerpt = []
    paras_seen = 0
    for line in content.splitlines():
        if not line.strip():
            paras_seen += 1
        if paras_seen < SPLIT_DEFAULT_PARAGRAPHS:
            default_excerpt.append(line)
        if line.strip() == SPLIT_MARKER:
            return '\n'.join(excerpt)
        excerpt.append(line)

    return '\n'.join(default_excerpt)

class SplitText(object):
    def __init__(self, instance, field_name, excerpt_field_name):
        # instead of storing actual values store a reference to the instance
        # along with field names, this makes assignment possible
        self.instance = instance
        self.field_name = field_name
        self.excerpt_field_name = excerpt_field_name

    # content is read/write
    def _get_content(self):
        return self.instance.__dict__[self.field_name]
    def _set_content(self, val):
        setattr(self.instance, self.field_name, val)
    content = property(_get_content, _set_content)

    # excerpt is a read only property
    def _get_excerpt(self):
        return getattr(self.instance, self.excerpt_field_name)
    excerpt = property(_get_excerpt)

    # has_more is a boolean property
    def _get_has_more(self):
        return self.excerpt.strip() != self.content.strip()
    has_more = property(_get_has_more)

    # allows display via templates without .content necessary
    def __unicode__(self):
        return self.content

class SplitDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.excerpt_field_name = _excerpt_field_name(self.field.name)

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        content = instance.__dict__[self.field.name]
        if content is None:
            return None
        return SplitText(instance, self.field.name, self.excerpt_field_name)

    def __set__(self, obj, value):
        if isinstance(value, SplitText):
            obj.__dict__[self.field.name] = value.content
            setattr(obj, self.excerpt_field_name, value.excerpt)
        else:
            obj.__dict__[self.field.name] = value

class SplitField(models.TextField):
    def __init__(self, *args, **kwargs):
        # for South FakeORM compatibility: the frozen version of a
        # SplitField can't try to add an _excerpt field, because the
        # _excerpt field itself is frozen as well. See introspection
        # rules below.
        self.add_excerpt_field = not kwargs.pop('no_excerpt_field', False)
        super(SplitField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        if self.add_excerpt_field and not cls._meta.abstract:
            excerpt_field = models.TextField(editable=False)
            cls.add_to_class(_excerpt_field_name(name), excerpt_field)
        super(SplitField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, SplitDescriptor(self))

    def pre_save(self, model_instance, add):
        value = super(SplitField, self).pre_save(model_instance, add)
        excerpt = get_excerpt(value.content)
        setattr(model_instance, _excerpt_field_name(self.attname), excerpt)
        return value.content

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return value.content

    def get_prep_value(self, value):
        try:
            return value.content
        except AttributeError:
            return value


# allow South to handle these fields smoothly
try:
    from south.modelsinspector import add_introspection_rules
    # For a normal MarkupField, the add_excerpt_field attribute is
    # always True, which means no_excerpt_field arg will always be
    # True in a frozen MarkupField, which is what we want.
    add_introspection_rules(rules=[
        (
            (SplitField,),
            [],
            {'no_excerpt_field': ('add_excerpt_field', {})}
        ),
        (
            (MonitorField,),
            [],
            {'monitor': ('monitor', {})}
        ),
        (
            (StatusField,),
            [],
            {'no_check_for_status': ('check_for_status', {})}
        ),
    ], patterns=['model_utils\.fields\.'])
except ImportError:
    pass

