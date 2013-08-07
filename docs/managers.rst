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

``InheritanceManager`` also provides a subclass-fetching alternative to the
``get()`` method:

.. code-block:: python

    place = Place.objects.get_subclass(id=some_id)
    # "place" will automatically be an instance of Place, Restaurant, or Bar

If you don't explicitly call ``select_subclasses()`` or ``get_subclass()``,
an ``InheritanceManager`` behaves identically to a normal ``Manager``; so
it's safe to use as your default manager for the model.

.. note::

    Due to `Django bug #16572`_, on Django versions prior to 1.6
    ``InheritanceManager`` only supports a single level of model inheritance;
    it won't work for grandchild models.

.. _contributed by Jeff Elmore: http://jeffelmore.org/2010/11/11/automatic-downcasting-of-inherited-models-in-django/
.. _Django bug #16572: https://code.djangoproject.com/ticket/16572


TimeStampedModel
----------------

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits from it.


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


PassThroughManager
------------------

A common "gotcha" when defining methods on a custom manager class is that those
same methods are not automatically also available on the QuerySets returned by
that manager, so are not "chainable". This can be counterintuitive, as most of
the public QuerySet API is mirrored on managers. It is possible to create a
custom Manager that returns QuerySets that have the same additional methods,
but this requires boilerplate code. The ``PassThroughManager`` class
(`contributed by Paul McLanahan`_) removes this boilerplate.

.. _contributed by Paul McLanahan: http://paulm.us/post/3717466639/passthroughmanager-for-django

To use ``PassThroughManager``, rather than defining a custom manager with
additional methods, define a custom ``QuerySet`` subclass with the additional
methods you want, and pass that ``QuerySet`` subclass to the
``PassThroughManager.for_queryset_class()`` class method. The returned
``PassThroughManager`` subclass will always return instances of your custom
``QuerySet``, and you can also call methods of your custom ``QuerySet``
directly on the manager:

.. code-block:: python

    from datetime import datetime
    from django.db import models
    from django.db.models.query import QuerySet
    from model_utils.managers import PassThroughManager

    class PostQuerySet(QuerySet):
        def by_author(self, user):
            return self.filter(user=user)

        def published(self):
            return self.filter(published__lte=datetime.now())

        def unpublished(self):
            return self.filter(published__gte=datetime.now())


    class Post(models.Model):
        user = models.ForeignKey(User)
        published = models.DateTimeField()

        objects = PassThroughManager.for_queryset_class(PostQuerySet)()

    Post.objects.published()
    Post.objects.by_author(user=request.user).unpublished()
