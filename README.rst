==================
django-model-utils
==================

Django model mixins and utilities.

Installation
============

Install from PyPI with ``pip``::

    pip install django-model-utils

or get the `in-development version`_::

    pip install django-model-utils==tip

.. _in-development version: http://bitbucket.org/carljm/django-model-utils/get/tip.gz#egg=django_model_utils-tip

To use ``django-model-utils`` in your Django project, just import and
use the utility classes described below; there is no need to modify
your ``INSTALLED_APPS`` setting.

Dependencies
------------

``django-model-utils`` requires `Django`_ 1.0 or later.

.. _Django: http://www.djangoproject.com/

Choices
=======

``Choices`` makes setting ``choices`` on a Django model field way
too easy::

    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        # ...
        status = models.CharField(choices=STATUS, default=STATUS.draft, max_length=20)

A ``Choices`` object is initialized with any number of choices, which
can either be a string ID or a tuple of (string ID, human-readable
version). If a string ID is given alone, the ID itself is used as the
human-readable version.

Accessing the string ID as an attribute on the ``Choices`` object
returns the string ID; this is a convenience for readable code in
assigning and testing values. 

When iterated over, a ``Choices`` object yields two-tuples linking id
to text names, the format expected by the ``choices`` attribute of
Django models. A ``Choices`` object can also be indexed into as if it
were a list of two-tuples.

.. note::
    Whither ``ChoiceEnum``? It's been deprecated in favor of ``Choices``.

StatusField
===========

A simple convenience for giving a model a set of "states."
``StatusField`` is a ``CharField`` subclass that expects to find a
``STATUS`` class attribute on its model, and uses that as its
``choices``. Also sets a default ``max_length`` of 100, and sets its
default value to the first item in the ``STATUS`` choices::

    from model_utils.fields import StatusField
    from model_utils import Choices
    
    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        # ...
        status = StatusField()

(The ``STATUS`` class attribute does not have to be a `Choices`_
instance, it can be an ordinary list of two-tuples).

MonitorField
============

A ``DateTimeField`` subclass that monitors another field on the model,
and updates itself to the current date-time whenever the monitored
field changes::

    from model_utils.fields import MonitorField, StatusField
    
    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        
        status = StatusField()
        status_changed = models.MonitorField(monitor='status')
        

SplitField
==========

A ``TextField`` subclass that automatically pulls an excerpt out of
its content (based on a "split here" marker or a default number of
initial paragraphs) and stores both its content and excerpt values in
the database.

A ``SplitField`` is easy to add to any model definition::

    from django.db import models
    from model_utils.fields import SplitField

    class Article(models.Model):
        title = models.CharField(max_length=100)
        body = SplitField()

``SplitField`` automatically creates an extra non-editable field
``_body_excerpt`` to store the excerpt. This field doesn't need to be
accessed directly; see below.

Accessing a SplitField on a model
---------------------------------

When accessing an attribute of a model that was declared as a
``SplitField``, a ``SplitText`` object is returned.  The ``SplitText``
object has three attributes:

``content``:
    The full field contents.
``excerpt``:
    The excerpt of ``content`` (read-only).
``has_more``:
    True if the excerpt and content are the same, False otherwise.

This object also has a ``__unicode__`` method that returns the full
content, allowing ``SplitField`` attributes to appear in templates
without having to access ``content`` directly.

Assuming the ``Article`` model above::

    >>> a = Article.objects.all()[0]
    >>> a.body.content
    u'some text\n\n<!-- split -->\n\nmore text'
    >>> a.body.excerpt
    u'some text\n'
    >>> unicode(a.body)
    u'some text\n\n<!-- split -->\n\nmore text'

Assignment to ``a.body`` is equivalent to assignment to
``a.body.content``.

.. note::
    a.body.excerpt is only updated when a.save() is called


Customized excerpting
---------------------

By default, ``SplitField`` looks for the marker ``<!-- split -->``
alone on a line and takes everything before that marker as the
excerpt. This marker can be customized by setting the ``SPLIT_MARKER``
setting.

If no marker is found in the content, the first two paragraphs (where
paragraphs are blocks of text separated by a blank line) are taken to
be the excerpt. This number can be customized by setting the
``SPLIT_DEFAULT_PARAGRAPHS`` setting.

TimeFramedModel
===============

An abstract base class for any model that expresses a time-range. Adds
``start`` and ``end`` nullable DateTimeFields, and a ``timeframed``
manager that returns only objects for whom the current date-time lies
within their time range.

StatusModel
===========

Pulls together `StatusField`_, `MonitorField`_ and `QueryManager`_
into an abstract base class for any model with a "status."

Just provide a ``STATUS`` class-attribute (a `Choices`_ object or a
list of two-tuples), and your model will have a ``status`` field with
those choices, a ``status_changed`` field containing the date-time the
``status`` was last changed, and a manager for each status that
returns objects with that status only::

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
        # ...
    
    class Restaurant(Place):
        # ...

    nearby_places = Place.objects.filter(location='here')
    for place in nearby_places:
        restaurant_or_bar = place.cast()
        # ...

.. note:: 
    This is inefficient for large querysets, as it results in n
    queries to the subtype tables.  It would be possible to write a
    QuerySet subclass that could reduce this to k queries, where there
    are k subtypes in the inheritance tree.

TimeStampedModel
================

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits from it.        
  

QueryManager
============

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

