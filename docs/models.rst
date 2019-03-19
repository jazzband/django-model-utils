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

This abstract base class just provides field ``is_removed`` which is
set to True instead of removing the instance. Entities returned in
default manager are limited to not-deleted instances.
