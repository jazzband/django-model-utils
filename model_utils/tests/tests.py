import django

# Needed for Django 1.4/1.5 test runner
if django.VERSION < (1, 6):
    from .test_fields import *
    from .test_managers import *
    from .test_models import *
    from .test_choices import *
    from .test_miscellaneous import *
