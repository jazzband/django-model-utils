Fields
======

.. _StatusField:

StatusField
-----------

A simple convenience for giving a model a set of "states."
``StatusField`` is a ``CharField`` subclass that expects to find a
class attribute called ``STATUS`` on its model or you can pass
``choices_name`` to use a different attribute name, and uses that as
its ``choices``. Also sets a default ``max_length`` of 100, and sets
its default value to the first item in the ``STATUS`` choices:

.. code-block:: python

    from model_utils.fields import StatusField
    from model_utils import Choices

    class Article(models.Model):
        STATUS = Choices('draft', 'published')
        # ...
        status = StatusField()

(The ``STATUS`` class attribute does not have to be a :ref:`Choices`
instance, it can be an ordinary list of two-tuples).

Using a different name for the model's choices class attribute

.. code-block:: python

    from model_utils.fields import StatusField
    from model_utils import Choices

    class Article(models.Model):
        ANOTHER_CHOICES = Choices('draft', 'published')
        # ...
        another_field = StatusField(choices_name='ANOTHER_CHOICES')

``StatusField`` does not set ``db_index=True`` automatically; if you
expect to frequently filter on your status field (and it will have
enough selectivity to make an index worthwhile) you may want to add this
yourself.


.. _MonitorField:

MonitorField
------------

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

If a list is passed to the ``when`` parameter, the field will only 
update when it matches one of the specified values:

.. code-block:: python

    from model_utils.fields import MonitorField, StatusField

    class Article(models.Model):
        STATUS = Choices('draft', 'published')

        status = StatusField()
        published_at = MonitorField(monitor='status', when=['published'])


SplitField
----------

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~

By default, ``SplitField`` looks for the marker ``<!-- split -->``
alone on a line and takes everything before that marker as the
excerpt. This marker can be customized by setting the ``SPLIT_MARKER``
setting.

If no marker is found in the content, the first two paragraphs (where
paragraphs are blocks of text separated by a blank line) are taken to
be the excerpt. This number can be customized by setting the
``SPLIT_DEFAULT_PARAGRAPHS`` setting.
