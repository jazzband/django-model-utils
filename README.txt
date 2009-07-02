==================
django-model-utils
==================

Django model mixins and utilities.

InheritanceCastModel
====================

This abstract base class can be inherited by the root (parent) model
in a model-inheritance tree.  It allows each model in the tree to
"know" what type it is (via an automatically-set foreign key to
``ContentType``), allowing for automatic casting of a parent instance
to its proper leaf (child) type.

For instance, if you have a ``Place`` model with subclasses
``Restaurant`` and ``Bar``, you may want to query all Places::

    nearby_places = Place.objects.filter(location='here')

But when you iterate over ``nearby_places``, you'll get only ``Place``
instances back, even for objects that are "really" ``Restaurant`` or
``Bar``.  If you have ``Place`` inherit from ``InheritanceCastModel``,
you can just call the ``cast()`` method on each ``Place`` and it will
return an instance of the proper subtype, ``Restaurant`` or ``Bar``::

    from model_utils.models import InheritanceCastModel

    class Place(InheritanceCastModel):
        ...
    
    class Restaurant(Place):
        ...

    nearby_places = Place.objects.filter(location='here')
    for place in nearby_places:
        restaurant_or_bar = place.cast()
        ...

.. note:: 
    This is inefficient for large querysets, as it results in n
    queries to the subtype tables.  It would be possible to write a
    QuerySet subclass that could reduce this to k queries, where there
    are k subtypes in the inheritance tree.

TimeStampedModel
================

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits it.
