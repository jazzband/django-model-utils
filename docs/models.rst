Models
======

TimeFramedModel
---------------

An abstract base class for any model that expresses a time-range. Adds
``start`` and ``end`` nullable DateTimeFields, and a ``timeframed``
manager that returns only objects for whom the current date-time lies
within their time range.


TimeStampedModel
----------------

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits from it.


StatusModel
-----------

Pulls together :ref:`StatusField`, :ref:`MonitorField` and :ref:`QueryManager`
into an abstract base class for any model with a "status."

Just provide a ``STATUS`` class-attribute (a :ref:`Choices` object or a
list of two-tuples), and your model will have a ``status`` field with
those choices, a ``status_changed`` field containing the date-time the
``status`` was last changed, and a manager for each status that
returns objects with that status only:

.. code-block:: python

    from model_utils.models import StatusModel
    from model_utils import Choices

    class Article(StatusModel):
        STATUS = Choices('draft', 'published')

    # ...

    a = Article()
    a.status = Article.STATUS.published

    # this save will update a.status_changed
    a.save()

    # this query will only return published articles:
    Article.published.all()


random_filename
---------------

A factory for random filenames to be used with the ``FileField``'s
``upload_to`` parameter.

The extension from the uploaded file is taken and used for the newly
generated filename.

``random_filename`` can take two arguments:

``directory``:
    The directory the uploaded file should be placed in. Defaults is blank.
``random_function``:
    A function that takes one argument, filename, and returns a random/unique
    representation of that filename.
    Default is ``uuid.uuid4``.


An example filename: `assets/270ef3e7-2105-4986-a8fb-6ef715273211.png`.


.. code-block:: python

   from django.db import models

   from model_utils.models import random_filename


   class Asset(models.Model):
       name = models.CharField(max_length=50)
       file = models.FileField(upload_to=random_filename('assets/'))
