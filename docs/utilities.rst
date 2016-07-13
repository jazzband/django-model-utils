=======================
Miscellaneous Utilities
=======================

.. _Choices:

Choices
=======

``Choices`` provides some conveniences for setting ``choices`` on a Django model field:

.. code-block:: python

    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices('draft', 'published')
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
        status = models.IntegerField(choices=STATUS, default=STATUS.draft)

You can index into a ``Choices`` instance to translate a database
representation to its display name:

.. code-block:: python

    status_display = Article.STATUS[article.status]

Option groups can also be used with ``Choices``; in that case each
argument is a tuple consisting of the option group name and a list of
options, where each option in the list is either a string, a two-tuple,
or a triple as outlined above. For example:

.. code-block:: python

    from model_utils import Choices

    class Article(models.Model):
    STATUS = Choices(('Visible', ['new', 'archived']), ('Invisible', ['draft', 'deleted']))

Choices can be concatenated with the ``+`` operator, both to other Choices
instances and other iterable objects that could be converted into Choices:

.. code-block:: python

    from model_utils import Choices

    GENERIC_CHOICES = Choices((0, 'draft', _('draft')), (1, 'published', _('published')))

    class Article(models.Model):
        STATUS = GENERIC_CHOICES + [(2, 'featured', _('featured'))]
        status = models.IntegerField(choices=STATUS, default=STATUS.draft)


Field Tracker
=============

A ``FieldTracker`` can be added to a model to track changes in model fields.  A
``FieldTracker`` allows querying for field changes since a model instance was
last saved.  An example of applying ``FieldTracker`` to a model:

.. code-block:: python

    from django.db import models
    from model_utils import FieldTracker

    class Post(models.Model):
        title = models.CharField(max_length=100)
        body = models.TextField()

        tracker = FieldTracker()

.. note::

    ``django-model-utils`` 1.3.0 introduced the ``ModelTracker`` object for
    tracking changes to model field values. Unfortunately ``ModelTracker``
    suffered from some serious flaws in its handling of ``ForeignKey`` fields,
    potentially resulting in many extra database queries if a ``ForeignKey``
    field was tracked. In order to avoid breaking API backwards-compatibility,
    ``ModelTracker`` retains the previous behavior but is deprecated, and
    ``FieldTracker`` has been introduced to provide better ``ForeignKey``
    handling. All uses of ``ModelTracker`` should be replaced by
    ``FieldTracker``.

    Summary of differences between ``ModelTracker`` and ``FieldTracker``:

    * The previous value returned for a tracked ``ForeignKey`` field will now
      be the raw ID rather than the full object (avoiding extra database
      queries). (GH-43)

    * The ``changed()`` method no longer returns the empty dictionary for all
      unsaved instances; rather, ``None`` is considered to be the initial value
      of all fields if the model has never been saved, thus ``changed()`` on an
      unsaved instance will return a dictionary containing all fields whose
      current value is not ``None``.

    * The ``has_changed()`` method no longer crashes after an object's first
      save. (GH-53).


Accessing a field tracker
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
Returns ``True`` if the given field has changed since the last save. The ``has_changed`` method expects a single field:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.title = 'Welcome'
    >>> a.tracker.has_changed('title')
    True
    >>> a.tracker.has_changed('body')
    False

The ``has_changed`` method relies on ``previous`` to determine whether a
field's values has changed.


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

The ``changed`` method relies on ``has_changed`` to determine which fields
have changed.


Tracking specific fields
------------------------

A fields parameter can be given to ``FieldTracker`` to limit tracking to
specific fields:

.. code-block:: python

    from django.db import models
    from model_utils import FieldTracker

    class Post(models.Model):
        title = models.CharField(max_length=100)
        body = models.TextField()

        title_tracker = FieldTracker(fields=['title'])

An example using the model specified above:

.. code-block:: pycon

    >>> a = Post.objects.create(title='First Post')
    >>> a.body = 'First post!'
    >>> a.title_tracker.changed()
    {'title': None}


Checking changes using signals
------------------------------

The field tracker methods may also be used in ``pre_save`` and ``post_save``
signal handlers to identify field changes on model save.

.. NOTE::

    Due to the implementation of ``FieldTracker``, ``post_save`` signal
    handlers relying on field tracker methods should only be registered after
    model creation.
