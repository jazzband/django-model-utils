from datetime import datetime

from django.db import models

class AutoCreatedField (models.DateTimeField):
    """
    A DateTimeField that automatically populates itself at
    object creation.

    By default, sets editable=False, default=datetime.now.

    """
    def __init__ (self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', datetime.now)
        super(AutoCreatedField, self).__init__(*args, **kwargs)

class AutoLastModifiedField (AutoCreatedField):
    """
    A DateTimeField that updates itself on each save() of the model.

    By default, sets editable=False and default=datetime.now.
    
    """
    def pre_save (self, model_instance, add):
        value = datetime.now()
        setattr(model_instance, self.attname, value)
        return value    
    
