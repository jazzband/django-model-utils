from pkg_resources import DistributionNotFound, get_distribution

from .choices import Choices  # noqa:F401
from .tracker import FieldTracker, ModelTracker  # noqa:F401

try:
    __version__ = get_distribution("django-model-utils").version
except DistributionNotFound:  # pragma: no cover
    # package is not installed
    __version__ = None
