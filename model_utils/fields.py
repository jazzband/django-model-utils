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


def _previous_status(model_instance, attname, add):
    if add:
        return None
    pk_value = getattr(model_instance, model_instance._meta.pk.attname)
    try:
        current = model_instance.__class__._default_manager.get(pk=pk_value)
    except model_instance.__class__.DoesNotExist:
        return None
    return getattr(current, attname, None)

class StatusField(models.CharField):
    """
    A CharField that has set status choices by default.

    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 100)
        super(StatusField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        if not cls._meta.abstract:
            assert hasattr(cls, 'STATUS'), \
                "The model '%s' doesn't have status choices." % cls.__name__
            setattr(self, '_choices', cls.STATUS)
            setattr(self, 'default', tuple(cls.STATUS)[0][0]) # sets first as default
        super(StatusField, self).contribute_to_class(cls, name)

    def pre_save(self, model_instance, add):
        previous = _previous_status(model_instance, 'get_%s_display' % self.attname, add)
        if previous:
            previous = previous()
        setattr(model_instance, 'previous_status', previous)
        return super(StatusField, self).pre_save(model_instance, add)

class StatusModifiedField(models.DateTimeField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', datetime.now)
        depends_on = kwargs.pop('depends_on', 'status')
        if not depends_on:
            raise TypeError(
                '%s requires a depends_on parameter' % self.__class__.__name__)
        self.depends_on = depends_on
        super(StatusModifiedField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        assert not getattr(cls._meta, "has_status_modified_field", False), "A model can't have more than one StatusModifiedField."
        super(StatusModifiedField, self).contribute_to_class(cls, name)
        setattr(cls._meta, "has_status_modified_field", True)

    def pre_save(self, model_instance, add):
        value = datetime.now()
        previous = _previous_status(model_instance, self.depends_on, add)
        current = getattr(model_instance, self.depends_on, None)
        if (previous and (previous != current)) or (current and not previous):
            setattr(model_instance, self.attname, value)
        return super(StatusModifiedField, self).pre_save(model_instance, add)


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
        if self.add_excerpt_field:
            excerpt_field = models.TextField(editable=False)
            excerpt_field.creation_counter = self.creation_counter+1
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

    def get_db_prep_value(self, value):
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
    add_introspection_rules(rules=[((SplitField,),
                                    [],
                                    {'no_excerpt_field': ('add_excerpt_field',
                                                          {})})],
                            patterns=['model_utils\.fields\.'])
except ImportError:
    pass

