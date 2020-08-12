Models
======

TimeFramedModel
---------------

An abstract base class for any model that expresses a time-range. Adds
``start`` and ``end`` nullable DateTimeFields, and provides a new
``timeframed`` manager on the subclass whose queryset pre-filters results
to only include those which have a ``start`` which is not in the future,
and an ``end`` which is not in the past. If either ``start`` or ``end`` is
``null``, the manager will include it.

.. code-block:: python

    from model_utils.models import TimeFramedModel
    from datetime import datetime, timedelta
    class Post(TimeFramedModel):
        pass

    p = Post()
    p.start = datetime.utcnow() - timedelta(days=1)
    p.end = datetime.utcnow() + timedelta(days=7)
    p.save()

    # this query will return the above Post instance:
    Post.timeframed.all()

    p.start = None
    p.end = None
    p.save()

    # this query will also return the above Post instance, because
    # the `start` and/or `end` are NULL.
    Post.timeframed.all()

    p.start = datetime.utcnow() + timedelta(days=7)
    p.save()

    # this query will NOT return our Post instance, because
    # the start date is in the future.
    Post.timeframed.all()

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


SoftDeletableModel
------------------

This abstract base class just provides a field ``is_removed`` which is
set to True instead of removing the instance. Entities returned in
manager ``available_objects`` are limited to not-deleted instances.

Note that relying on the default ``objects`` manager to filter out not-deleted
instances is deprecated. ``objects`` will include deleted objects in a future
release.


UUIDModel
------------------

This abstract base class provides ``id`` field on any model that inherits from it
which will be the primary key.

If you dont want to set ``id`` as primary key or change the field name, you can be override it
with our `UUIDField`_

Also you can override the default uuid version. Versions 1,3,4 and 5 are now supported.

.. code-block:: python

    from model_utils.models import UUIDModel

    class MyAppModel(UUIDModel):
        pass


.. _`UUIDField`: https://github.com/jazzband/django-model-utils/blob/master/docs/fields.rst#uuidfield


SaveSignalHandlingModel
-----------------------

An abstract base class model to pass a parameter ``signals_to_disable``
to ``save`` method in order to disable signals

.. code-block:: python

    from model_utils.models import SaveSignalHandlingModel

    class SaveSignalTestModel(SaveSignalHandlingModel):
        name = models.CharField(max_length=20)

    obj = SaveSignalTestModel(name='Test')
    # Note: If you use `Model.objects.create`, the signals can't be disabled
    obj.save(signals_to_disable=['pre_save'] # disable `pre_save` signal
