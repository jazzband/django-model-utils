
try:
    from unittest import skipUnless
except ImportError: # Python 2.6
    from django.utils.unittest import skipUnless
