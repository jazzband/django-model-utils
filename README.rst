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

Most of ``django-model-utils`` works with `Django`_ 1.0 or later.
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

If you don't explicitly call ``select_subclasses()``, an ``InheritanceManager``
behaves identically to a normal ``Manager``; so it's safe to use as your
default manager for the model.

.. note::
    ``InheritanceManager`` currently only supports a single level of model
    inheritance; it won't work for grandchild models.

.. note::
    ``InheritanceManager`` requires Django 1.2 or later.

.. _contributed by Jeff Elmore: http://jeffelmore.org/2010/11/11/automatic-downcasting-of-inherited-models-in-django/


InheritanceCastModel
====================

This abstract base class can be inherited by the root (parent) model in a
model-inheritance tree. It solves the same problem as `InheritanceManager`_ in
a way that requires more database queries and is less convenient to use, but is
compatible with Django versions prior to 1.2. Whenever possible,
`InheritanceManager`_ should be used instead.

Usage::

    from model_utils.models import InheritanceCastModel

    class Place(InheritanceCastModel):
        # ...

    class Restaurant(Place):
        # ...

    class Bar(Place):
        # ...

    nearby_places = Place.objects.filter(location='here')
    for place in nearby_places:
        restaurant_or_bar = place.cast() # ...

This is inefficient for large querysets, as it results in a new query for every
individual returned object.  You can use the ``cast()`` method on a queryset to
reduce this to as many queries as subtypes are involved::

    nearby_places = Place.objects.filter(location='here')
    for place in nearby_places.cast():
        # ...

.. note::
    The ``cast()`` queryset method does *not* return another queryset but an
    already evaluated result of the database query.  This means that you cannot
    chain additional queryset methods after ``cast()``.

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

manager_from
============

A common "gotcha" when defining methods on a custom manager class is
that those same methods are not automatically also available on the
QuerySet used by that model, so are not "chainable". This can be
counterintuitive, as most of the public QuerySet API is also available
on managers. It is possible to create a custom Manager that returns
QuerySets that have the same additional methods, but this requires
boilerplate code.

The ``manager_from`` function (`created by George Sakkis`_ and
included here by permission) solves this problem with zero
boilerplate. It creates and returns a Manager subclass with additional
behavior defined by mixin subclasses or functions you pass it, and the
returned Manager will return instances of a custom QuerySet with those
same additional methods::

    from datetime import datetime
    from django.db import models
    
    class AuthorMixin(object):
        def by_author(self, user):
            return self.filter(user=user)
    
    class PublishedMixin(object):
        def published(self):
            return self.filter(published__lte=datetime.now())
    
    def unpublished(self):
        return self.filter(published__gte=datetime.now())
    
    
    class Post(models.Model):
        user = models.ForeignKey(User)
        published = models.DateTimeField()
    
        objects = manager_from(AuthorMixin, PublishedMixin, unpublished)
    
    Post.objects.published()
    Post.objects.by_author(user=request.user).unpublished()

.. _created by George Sakkis: http://djangosnippets.org/snippets/2117/

PassThroughManager
==================

The ``PassThroughManager`` class (`contributed by Paul McLanahan`_) solves
the same problem as the above ``manager_from`` function. This class, however,
accomplishes it in a different way. The reason it exists is that the dynamically
generated ``QuerySet`` classes created by the ``manager_from`` function are
not picklable. It's probably not often that a ``QuerySet`` is pickled, but
it is a documented feature of the Django ``QuerySet`` class, and this method
maintains that functionality.

``PassThroughManager`` is a subclass of ``django.db.models.manager.Manager``,
so all that is required is that you change your custom managers to inherit from
``PassThroughManager`` instead of Django's built-in ``Manager`` class. Once you
do this, create your custom ``QuerySet`` class, and have your manager's
``get_query_set`` method return instances of said class, then all of the
methods you add to your custom ``QuerySet`` class will be available from your
manager as well::

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
            PostQuerySet(self.model, using=self._db)
        
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

Alternatively, if you don't need any methods on your manager that shouldn't also
be on your queryset, a shortcut is available. ``PassThroughManager``'s
constructor takes an optional argument. If you pass it a ``QuerySet`` subclass
it will automatically use that class when creating querysets for the manager::

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

.. _contributed by Paul McLanahan: http://paulm.us/post/3717466639/passthroughmanager-for-django

