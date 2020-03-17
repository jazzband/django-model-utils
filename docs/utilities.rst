=======================
Miscellaneous Utilities
=======================

.. _Choices:

``Choices``
===========

.. note::

    Django 3.0 adds `enumeration types <https://docs.djangoproject.com/en/3.0/releases/3.0/#enumerations-for-model-field-choices>`__.
    These provide most of the same features as ``Choices``.

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

Should you wish to provide a subset of choices for a field, for
instance, you have a form class to set some model instance to a failed
state, and only wish to show the user the failed outcomes from which to
select, you can use the ``subset`` method:

.. code-block:: python

    from model_utils import Choices

    OUTCOMES = Choices(
        (0, 'success', _('Successful')),
        (1, 'user_cancelled', _('Cancelled by the user')),
        (2, 'admin_cancelled', _('Cancelled by an admin')),
    )
    FAILED_OUTCOMES = OUTCOMES.subset('user_cancelled', 'admin_cancelled')

The ``choices`` attribute on the model field can then be set to
``FAILED_OUTCOMES``, thus allowing the subset to be defined in close
proximity to the definition of all the choices, and reused elsewhere as
required.


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

If a field is `deferred`_, calling ``previous()`` will load the previous value from the database.

.. _deferred: https://docs.djangoproject.com/en/2.0/ref/models/querysets/#defer


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

If a field is `deferred`_ and has been assigned locally, calling ``has_changed()``
will load the previous value from the database to perform the comparison.

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


Tracking Foreign Key Fields
---------------------------

It should be noted that a generic FieldTracker tracks Foreign Keys by db_column name, rather than model field name, and would be accessed as follows:

.. code-block:: python

    from django.db import models
    from model_utils import FieldTracker

    class Parent(models.Model):
        name = models.CharField(max_length=64)

    class Child(models.Model):
        name = models.CharField(max_length=64)
        parent = models.ForeignKey(Parent)
        tracker = FieldTracker()

.. code-block:: pycon

    >>> p = Parent.objects.create(name='P')
    >>> c = Child.objects.create(name='C', parent=p)
    >>> c.tracker.has_changed('parent_id')


To find the db_column names of your model (using the above example):

.. code-block:: pycon

    >>> for field in Child._meta.fields:
            field.get_attname_column()
    ('id', 'id')
    ('name', 'name')
    ('parent_id', 'parent_id')


The model field name *may* be used when tracking with a specific tracker:

.. code-block:: python

    specific_tracker = FieldTracker(fields=['parent'])

But according to issue #195 this is not recommended for accessing Foreign Key Fields.


Checking changes using signals
------------------------------

The field tracker methods may also be used in ``pre_save`` and ``post_save``
signal handlers to identify field changes on model save.

.. NOTE::

    Due to the implementation of ``FieldTracker``, ``post_save`` signal
    handlers relying on field tracker methods should only be registered after
    model creation.

FieldTracker implementation details
-----------------------------------

.. code-block:: python

    from django.db import models
    from model_utils import FieldTracker, TimeStampedModel

    class MyModel(TimeStampedModel):
        name = models.CharField(max_length=64)
        tracker = FieldTracker()

        def save(self, *args, **kwargs):
            """ Automatically add "modified" to update_fields."""
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'modified'}
            super().save(*args, **kwargs)

    # [...]

    instance = MyModel.objects.first()
    instance.name = 'new'
    instance.save(update_fields={'name'})

This is how ``FieldTracker`` tracks field changes on ``instance.save`` call.

1. In ``class_prepared`` handler ``FieldTracker`` patches ``save_base`` and
   ``refresh_from_db`` methods to reset initial state for tracked fields.
2. In ``post_init`` handler ``FieldTracker`` saves initial values for tracked
   fields.
3. ``MyModel.save`` changes ``update_fields`` in order to store auto updated
   ``modified`` timestamp. Complete list of saved fields is now known.
4. ``Model.save`` does nothing interesting except calling ``save_base``.
5. Decorated ``save_base()`` method calls ``super().save_base`` and all fields
   that have values different to initial are considered as changed.
6. ``Model.save_base`` sends ``pre_save`` signal, saves instance to database and
   sends ``post_save`` signal. All ``pre_save/post_save`` receivers can query
   ``instance.tracker`` for a set of changed fields etc.
7. After ``Model.save_base`` return ``FieldTracker`` resets initial state for
   updated fields (if no ``update_fields`` passed - whole initial state is
   reset).
8. ``instance.refresh_from_db()`` call causes initial state reset like for
   ``save_base()``.

