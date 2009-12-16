==================
django-model-utils
==================

Django model mixins and utilities.

Installation
============

Install from PyPI with ``easy_install`` or ``pip``::

    pip install django-model-utils

or get the `in-development version`_::

    pip install django-model-utils==tip

.. _in-development version: http://bitbucket.org/carljm/django-model-utils/get/tip.gz#egg=django_model_utils-tip

To use ``django-model-utils`` in your Django project, just import the
utility classes described below; there is no need to modify your
``INSTALLED_APPS`` setting.

Dependencies
------------

``django-model-utils`` requires `Django`_ 1.0 or later.

.. _Django: http://www.djangoproject.com/

models.InheritanceCastModel
===========================

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

models.TimeStampedModel
=======================

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits it.

managers.QueryManager
=====================

Many custom model managers do nothing more than return a QuerySet that
is filtered in some way. ``QueryManager`` allows you to express this
pattern with a minimum of boilerplate::

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
