Model Managers
==============

InheritanceManager
------------------

This manager (`contributed by Jeff Elmore`_) should be attached to a base model
class in a model-inheritance tree.  It allows queries on that base model to
return heterogenous results of the actual proper subtypes, without any
additional queries.

For instance, if you have a ``Place`` model with subclasses ``Restaurant`` and
``Bar``, you may want to query all Places:

.. code-block:: python

    nearby_places = Place.objects.filter(location='here')

But when you iterate over ``nearby_places``, you'll get only ``Place``
instances back, even for objects that are "really" ``Restaurant`` or ``Bar``.
If you attach an ``InheritanceManager`` to ``Place``, you can just call the
``select_subclasses()`` method on the ``InheritanceManager`` or any
``QuerySet`` from it, and the resulting objects will be instances of
``Restaurant`` or ``Bar``:

.. code-block:: python

    from model_utils.managers import InheritanceManager

    class Place(models.Model):
        # ...
        objects = InheritanceManager()

    class Restaurant(Place):
        # ...

    class Bar(Place):
        # ...

    nearby_places = Place.objects.filter(location='here').select_subclasses()
    for place in nearby_places:
        # "place" will automatically be an instance of Place, Restaurant, or Bar

The database query performed will have an extra join for each subclass; if you
want to reduce the number of joins and you only need particular subclasses to
be returned as their actual type, you can pass subclass names to
``select_subclasses()``, much like the built-in ``select_related()`` method:

.. code-block:: python

    nearby_places = Place.objects.select_subclasses("restaurant")
    # restaurants will be Restaurant instances, bars will still be Place instances

    nearby_places = Place.objects.select_subclasses("restaurant", "bar")
    # all Places will be converted to Restaurant and Bar instances.

It is also possible to use the subclasses themselves as arguments to
``select_subclasses``, leaving it to calculate the relationship for you:

.. code-block:: python

    nearby_places = Place.objects.select_subclasses(Restaurant)
    # restaurants will be Restaurant instances, bars will still be Place instances

    nearby_places = Place.objects.select_subclasses(Restaurant, Bar)
    # all Places will be converted to Restaurant and Bar instances.

It is even possible to mix and match the two:

.. code-block:: python

    nearby_places = Place.objects.select_subclasses(Restaurant, "bar")
    # all Places will be converted to Restaurant and Bar instances.

``InheritanceManager`` also provides a subclass-fetching alternative to the
``get()`` method:

.. code-block:: python

    place = Place.objects.get_subclass(id=some_id)
    # "place" will automatically be an instance of Place, Restaurant, or Bar

If you don't explicitly call ``select_subclasses()`` or ``get_subclass()``,
an ``InheritanceManager`` behaves identically to a normal ``Manager``; so
it's safe to use as your default manager for the model.

.. _contributed by Jeff Elmore: http://jeffelmore.org/2010/11/11/automatic-downcasting-of-inherited-models-in-django/


.. _QueryManager:

QueryManager
------------

Many custom model managers do nothing more than return a QuerySet that
is filtered in some way. ``QueryManager`` allows you to express this
pattern with a minimum of boilerplate:

.. code-block:: python

    from django.db import models
    from model_utils.managers import QueryManager

    class Post(models.Model):
        ...
        published = models.BooleanField()
        pub_date = models.DateField()
        ...

        objects = models.Manager()
        public = QueryManager(published=True).order_by('-pub_date')

The kwargs passed to ``QueryManager`` will be passed as-is to the
``QuerySet.filter()`` method. You can also pass a ``Q`` object to
``QueryManager`` to express more complex conditions. Note that you can
set the ordering of the ``QuerySet`` returned by the ``QueryManager``
by chaining a call to ``.order_by()`` on the ``QueryManager`` (this is
not required).

SoftDeletableManager
--------------------

Returns only model instances that have the ``is_removed`` field set
to False. Uses ``SoftDeletableQuerySet``, which ensures model instances
won't be removed in bulk, but they will be marked as removed instead.

Mixins
------

Each of the above manager classes has a corresponding mixin that can be used to
add functionality to any manager.

Note that any manager class using ``InheritanceManagerMixin`` must return a
``QuerySet`` class using ``InheritanceQuerySetMixin`` from its ``get_queryset``
method.
