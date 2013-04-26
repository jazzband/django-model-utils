==================
django-model-utils
==================

.. image:: https://secure.travis-ci.org/carljm/django-model-utils.png?branch=master
   :target: http://travis-ci.org/carljm/django-model-utils
.. image:: https://coveralls.io/repos/carljm/django-model-utils/badge.png?branch=master
   :target: https://coveralls.io/r/carljm/django-model-utils

Django model mixins and utilities.

Installation
============

Install from PyPI with ``pip``::

    pip install django-model-utils

To use ``django-model-utils`` in your Django project, just import and
use the utility classes described below; there is no need to modify
your ``INSTALLED_APPS`` setting.

Dependencies
------------

``django-model-utils`` supports `Django`_ 1.4.2 and later on Python 2.6, 2.7,
3.2, and 3.3.

.. _Django: http://www.djangoproject.com/


Contributing
============

Please file bugs and send pull requests to the `GitHub repository`_ and `issue
tracker`_.

.. _GitHub repository: https://github.com/carljm/django-model-utils/
.. _issue tracker: https://github.com/carljm/django-model-utils/issues

(Until January 2013 django-model-utils primary development was hosted at
`BitBucket`_; the issue tracker there will remain open until all issues and
pull requests tracked in it are closed, but all new issues should be filed at
GitHub.)

.. _BitBucket: https://bitbucket.org/carljm/django-model-utils/overview


Choices
=======

``Choices`` provides some conveniences for setting ``choices`` on a Django model field:

.. code-block:: python

    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        # ...
        status = models.CharField(choices=STATUS, default=STATUS.draft, max_length=20)

A ``Choices`` object is initialized with any number of choices. In the
simplest case, each choice is a string; that string will be used both
as the database representation of the choice, and the human-readable
representation. Note that you can access options as attributes on the
``Choices`` object: ``STATUS.draft``.

But you may want your human-readable versions translated, in which
case you need to separate the human-readable version from the DB
representation. In this case you can provide choices as two-tuples:

.. code-block:: python

    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices(('draft', _('draft')), ('published', _('published')))
        # ...
        status = models.CharField(choices=STATUS, default=STATUS.draft, max_length=20)

But what if your database representation of choices is constrained in
a way that would hinder readability of your code? For instance, you
may need to use an ``IntegerField`` rather than a ``CharField``, or
you may want the database to order the values in your field in some
specific way. In this case, you can provide your choices as triples,
where the first element is the database representation, the second is
a valid Python identifier you will use in your code as a constant, and
the third is the human-readable version:

.. code-block:: python

    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices((0, 'draft', _('draft')), (1, 'published', _('published')))
        # ...
        status = models.IntegerField(choices=STATUS, default=STATUS.draft)


StatusField
===========

A simple convenience for giving a model a set of "states."
``StatusField`` is a ``CharField`` subclass that expects to find a
``STATUS`` class attribute on its model, and uses that as its
``choices``. Also sets a default ``max_length`` of 100, and sets its
default value to the first item in the ``STATUS`` choices:

.. code-block:: python

    from model_utils.fields import StatusField
    from model_utils import Choices
    
    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        # ...
        status = StatusField()

(The ``STATUS`` class attribute does not have to be a `Choices`_
instance, it can be an ordinary list of two-tuples).

``StatusField`` does not set ``db_index=True`` automatically; if you
expect to frequently filter on your status field (and it will have
enough selectivity to make an index worthwhile) you may want to add this
yourself.


MonitorField
============

A ``DateTimeField`` subclass that monitors another field on the model,
and updates itself to the current date-time whenever the monitored
field changes:

.. code-block:: python

    from model_utils.fields import MonitorField, StatusField
    
    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        
        status = StatusField()
        status_changed = MonitorField(monitor='status')

(A ``MonitorField`` can monitor any type of field for changes, not only a
``StatusField``.)

SplitField
==========

A ``TextField`` subclass that automatically pulls an excerpt out of
its content (based on a "split here" marker or a default number of
initial paragraphs) and stores both its content and excerpt values in
the database.

A ``SplitField`` is easy to add to any model definition:

.. code-block:: python

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
    True if the excerpt and content are different, False otherwise.

This object also has a ``__unicode__`` method that returns the full
content, allowing ``SplitField`` attributes to appear in templates
without having to access ``content`` directly.

Assuming the ``Article`` model above:

.. code-block:: pycon

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

InheritanceManager
==================

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

.. note::
    The implementation of ``InheritanceManager`` uses ``select_related``
    internally.  Due to `Django bug #16855`_, this currently means that it
    will override any previous ``select_related`` calls on the ``QuerySet``.

.. _contributed by Jeff Elmore: http://jeffelmore.org/2010/11/11/automatic-downcasting-of-inherited-models-in-django/
.. _Django bug #16855: https://code.djangoproject.com/ticket/16855
.. _Django bug #16572: https://code.djangoproject.com/ticket/16572


TimeStampedModel
================

This abstract base class just provides self-updating ``created`` and
``modified`` fields on any model that inherits from it.

QueryManager
============

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
==================

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


ModelTracker
============

A ``ModelTracker`` can be added to a model to track changes in model fields.  A
``ModelTracker`` allows querying for field changes since a model instance was
last saved.  An example of applying ``ModelTracker`` to a model:

.. code-block:: python

    from django.db import models
    from model_utils import ModelTracker

    class Post(models.Model):
        title = models.CharField(max_length=100)
        body = models.TextField()

        tracker = ModelTracker()

Accessing a model tracker
-------------------------

There are multiple methods available for checking for changes in model fields.

previous
~~~~~~~~
Returns the value of the given field during the last save:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.title = 'Welcome'
    >>> a.tracker.previous('title')
    u'First Post'

Returns ``None`` when the model instance isn't saved yet.

has_changed
~~~~~~~~~~~
Returns ``True`` if the given field has changed since the last save:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.title = 'Welcome'
    >>> a.tracker.has_changed('title')
    True
    >>> a.tracker.has_changed('body')
    False

Returns ``True`` if the model instance hasn't been saved yet.

changed
~~~~~~~
Returns a dictionary of all fields that have been changed since the last save
and the values of the fields during the last save:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.title = 'Welcome'
    >>> a.body = 'First post!'
    >>> a.tracker.changed()
    {'title': 'First Post', 'body': ''}

Returns ``{}`` if the model instance hasn't been saved yet.


Tracking specific fields
------------------------

A fields parameter can be given to ``ModelTracker`` to limit model tracking to
the specific fields:

.. code-block:: python

    from django.db import models
    from model_utils import ModelTracker

    class Post(models.Model):
        title = models.CharField(max_length=100)
        body = models.TextField()

        title_tracker = ModelTracker(fields=['title'])

An example using the model specified above:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.body = 'First post!'
    >>> a.title_tracker.changed()
    {}

