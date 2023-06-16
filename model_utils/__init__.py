import importlib.metadata

from .choices import Choices  # noqa:F401
from .tracker import FieldTracker, ModelTracker  # noqa:F401

try:
    __version__ = importlib.metadata.version('django-model-utils')
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = None
