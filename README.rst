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

.. _in-development version: http://bitbucket.org/carljm/django-model-utils/get/tip.tar.gz#egg=django_model_utils-tip

To use ``django-model-utils`` in your Django project, just import and
use the utility classes described below; there is no need to modify
your ``INSTALLED_APPS`` setting.

Dependencies
------------

Most of ``django-model-utils`` works with `Django`_ 1.1 or later.
`InheritanceManager`_ and `SplitField`_ require Django 1.2 or later.

.. _Django: http://www.djangoproject.com/

Choices
=======

``Choices`` provides some conveniences for setting ``choices`` on a Django model field::

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
representation. In this case you can provide choices as two-tuples::

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
the third is the human-readable version::

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
        status_changed = MonitorField(monitor='status')

(A ``MonitorField`` can monitor any type of field for changes, not only a
``StatusField``.)

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

InheritanceManager
==================

This manager (`contributed by Jeff Elmore`_) should be attached to a base model
class in a model-inheritance tree.  It allows queries on that base model to
return heterogenous results of the actual proper subtypes, without any
additional queries.

For instance, if you have a ``Place`` model with subclasses ``Restaurant`` and
``Bar``, you may want to query all Places::

    nearby_places = Place.objects.filter(location='here')

But when you iterate over ``nearby_places``, you'll get only ``Place``
instances back, even for objects that are "really" ``Restaurant`` or ``Bar``.
If you attach an ``InheritanceManager`` to ``Place``, you can just call the
``select_subclasses()`` method on the ``InheritanceManager`` or any
``QuerySet`` from it, and the resulting objects will be instances of
``Restaurant`` or ``Bar``::

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
``select_subclasses()``, much like the built-in ``select_related()`` method::

    nearby_places = Place.objects.select_subclasses("restaurant")
    # restaurants will be Restaurant instances, bars will still be Place instances

``InheritanceManager`` also provides a subclass-fetching alternative to the
``get()`` method::
    
    place = Place.objects.get_subclass(id=some_id)
    # "place" will automatically be an instance of Place, Restaurant, or Bar

If you don't explicitly call ``select_subclasses()`` or ``get_subclass()``,
an ``InheritanceManager`` behaves identically to a normal ``Manager``; so
it's safe to use as your default manager for the model.

.. note::
    ``InheritanceManager`` currently only supports a single level of model
    inheritance; it won't work for grandchild models.

.. note::
    ``InheritanceManager`` requires Django 1.2 or later. Previous versions of
    django-model-utils included ``InheritanceCastModel``, an alternative (and
    inferior) approach to this problem that is Django 1.1
    compatible. ``InheritanceCastModel`` will remain in django-model-utils
    until support for Django 1.1 is removed, but it is no longer documented and
    its use in new code is discouraged.

.. _contributed by Jeff Elmore: http://jeffelmore.org/2010/11/11/automatic-downcasting-of-inherited-models-in-django/


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
``PassThroughManager`` constructor. ``PassThroughManager`` will always return
instances of your custom ``QuerySet``, and you can also call methods of your
custom ``QuerySet`` directly on the manager::

    from datetime import datetime
    from django.db import models
    from django.db.models.query import QuerySet
    
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
    
        objects = PassThroughManager(PostQuerySet)
    
    Post.objects.published()
    Post.objects.by_author(user=request.user).unpublished()

If you want certain methods available only on the manager, or you need to
override other manager methods (particularly ``get_query_set``), you can also
define a custom manager that inherits from ``PassThroughManager``::

    from datetime import datetime
    from django.db import models
    from django.db.models.query import QuerySet
    
    class PostQuerySet(QuerySet):
        def by_author(self, user):
            return self.filter(user=user)
    
        def published(self):
            return self.filter(published__lte=datetime.now())
    
        def unpublished(self):
            return self.filter(published__gte=datetime.now())
    
    class PostManager(PassThroughManager):
        def get_query_set(self):
            return PostQuerySet(self.model, using=self._db)
    
        def get_stats(self):
            return {
                'published_count': self.published().count(),
                'unpublished_count': self.unpublished().count(),
            }
    
    class Post(models.Model):
        user = models.ForeignKey(User)
        published = models.DateTimeField()
    
        objects = PostManager()
    
    Post.objects.get_stats()
    Post.objects.published()
    Post.objects.by_author(user=request.user).unpublished()

.. note::

   Previous versions of django-model-utils included ``manager_from``, a
   function that solved the same problem as ``PassThroughManager``. The
   ``manager_from`` approach created dynamic ``QuerySet`` subclasses on the
   fly, which broke pickling of those querysets. For this reason,
   ``PassThroughManager`` is recommended instead.

If you would like your custom ``QuerySet`` methods available through related
managers, use the convenience ``PassThroughManager.for_queryset_class``. For
example::

    class Post(models.Model):
        user = models.ForeignKey(User)
        published = models.DateTimeField()

        objects = PassThroughManager.for_queryset_class(PostQuerySet)()

Now you will be able to make queries like::

    >>> u = User.objects.all()[0]
    >>> a.post_set.published()
