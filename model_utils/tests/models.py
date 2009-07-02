from django.db import models

from model_utils.models import InheritanceCastModel, TimeStampedModel

class InheritParent(InheritanceCastModel):
    pass

class InheritChild(InheritParent):
    pass

class TimeStamp(TimeStampedModel):
    pass
