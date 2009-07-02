from django.db import models

from model_utils.models import InheritanceCastModel

class InheritParent(InheritanceCastModel):
    pass

class InheritChild(InheritParent):
    pass

