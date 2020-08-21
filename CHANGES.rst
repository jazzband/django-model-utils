CHANGES
=======

4.0.1 (unreleased)
------------------
- Update InheritanceQuerySetMixin to avoid querying too much tables
- TimeStampedModel now automatically adds 'modified' field as an update_fields
  parameter even if it is forgotten while using save()
- `FieldTracker` now marks fields as not changed after `refresh_from_db`
- `FieldTracker` now respects `update_fields` changed in overridden `save()`
  method
- Replace ugettext_lazy with gettext_lazy to satisfy Django deprecation warning
- Add available_objects manager to SoftDeletableModel and add deprecation
  warning to objects manager.

4.0.0 (2019-12-11)
------------------
- Added `Choices.subset`.
- Remove hacks for previously supported Django versions. (Fixes GH-390)
- Dropped support for Python 2.7. (Fixes GH-393)
- Dropped usage of `six`
- Drop support for `Django 1.11`
- Add support for `Python 3.8`
- Add support for `Django 3.0`

3.2.0 (2019.06.21)
-------------------
- Catch `AttributeError` for deferred abstract fields, fixes GH-331.
- Update documentation to explain usage of `timeframed` model manager, fixes GH-118
- Honor `OneToOneField.parent_link=False`.
- Fix handling of deferred attributes on Django 1.10+, fixes GH-278
- Fix `FieldTracker.has_changed()` and `FieldTracker.previous()` to return
  correct responses for deferred fields.
- Add Simplified Chinese translations.
- Update AutoLastModifiedField so that at instance creation it will
  always be set equal to created to make querying easier. Fixes GH-254
- Support `reversed` for all kinds of `Choices` objects, fixes GH-309
- Fix Model instance non picklable GH-330
- Fix patched `save` in FieldTracker
- Upgrades test requirements (pytest, pytest-django, pytest-cov) and
  skips tox test with Python 3.5 and Django (trunk)
- Add UUIDModel and UUIDField support.

3.1.2 (2018.05.09)
------------------
- Update InheritanceIterable to inherit from
  ModelIterable instead of BaseIterable, fixes GH-277.

- Add all_objects Manager for 'SoftDeletableModel' to include soft
  deleted objects on queries as per issue GH-255

3.1.1 (2017.12.17)
------------------

- Update classifiers and README via GH-306, fixes GH-305

3.1.0 (2017.12.11)
------------------

- Support for Django 2.0 via GH-298, fixes GH-297
- Remove old travis script via GH-300
- Fix codecov and switch to py.test #301

3.0.0 (2017.04.13)
------------------

- Drop support for Python 2.6.
- Drop support for Django 1.4, 1.5, 1.6, 1.7.
- Exclude tests from the distribution, fixes GH-258.
- Add support for Django 1.11 GH-269
- Add a new model to disable pre_save/post_save signals


2.6.1 (2017.01.11)
------------------

- Fix infinite recursion with multiple `MonitorField` and `defer()` or `only()`
  on Django 1.10+. Thanks Romain Garrigues. Merge of GH-242, fixes GH-241.

- Fix `InheritanceManager` and `SoftDeletableManager` to respect
  `self._queryset_class` instead of hardcoding the queryset class. Merge of
  GH-250, fixes GH-249.

- Add mixins for `SoftDeletableQuerySet` and `SoftDeletableManager`, as stated
  in the the documentation.

- Fix `SoftDeletableModel.delete()` to use the correct database connection.
  Merge of GH-239.

- Added boolean keyword argument `soft` to `SoftDeletableModel.delete()` that
  revert to default behavior when set to `False`. Merge of GH-240.

- Enforced default manager in `StatusModel` to avoid manager order issues when
  using abstract models that redefine `objects` manager. Merge of GH-253, fixes
  GH-251.


2.6 (2016.09.19)
----------------

- Added `SoftDeletableModel` abstract class, its manageer
  `SoftDeletableManager` and queryset `SoftDeletableQuerySet`.

- Fix issue with field tracker and deferred FileField for Django 1.10.


2.5.2 (2016.08.09)
------------------

- Include `runtests.py` in sdist.


2.5.1 (2016.08.03)
------------------

- Fix `InheritanceQuerySet` raising an `AttributeError` exception
  under Django 1.9.

- Django 1.10 support regressed with changes between pre-alpha and final
  release; 1.10 currently not supported.


2.5 (2016.04.18)
----------------

- Drop support for Python 3.2.

- Add support for Django 1.10 pre-alpha.

- Track foreign keys on parent models properly when a tracker
  is defined on a child model. Fixes GH-214.


2.4 (2015.12.03)
----------------

- Remove `PassThroughManager`. Use Django's built-in `QuerySet.as_manager()`
  and/or `Manager.from_queryset()` utilities instead.

- Add support for Django 1.9.


2.3.1 (2015-07-20)
------------------

- Remove all translation-related automation in `setup.py`. Fixes GH-178 and
  GH-179. Thanks Joe Weiss, Matt Molyneaux, and others for the reports.


2.3 (2015.07.17)
----------------

- Keep track of deferred fields on model instance instead of on
  FieldInstanceTracker instance. Fixes accessing deferred fields for multiple
  instances of a model from the same queryset. Thanks Bram Boogaard. Merge of
  GH-151.

- Fix Django 1.7 migrations compatibility for SplitField. Thanks ad-m. Merge of
  GH-157; fixes GH-156.

- Add German translations.

- Django 1.8 compatibility.


2.2 (2014.07.31)
----------------

- Revert GH-130, restoring ability to access ``FieldTracker`` changes in
  overridden ``save`` methods or ``post_save`` handlers. This reopens GH-83
  (inability to pickle models with ``FieldTracker``) until a solution can be
  found that doesn't break behavior otherwise. Thanks Brian May for the
  report. Fixes GH-143.


2.1.1 (2014.07.28)
------------------

- ASCII-fold all non-ASCII characters in changelog; again. Argh. Apologies to
  those whose names are mangled by this change. It seems that distutils makes
  it impossible to handle non-ASCII content reliably under Python 3 in a
  setup.py long_description, when the system encoding may be ASCII. Thanks
  Brian May for the report. Fixes GH-141.


2.1.0 (2014.07.25)
------------------

- Add support for Django's built-in migrations to ``MonitorField`` and
  ``StatusField``.

- ``PassThroughManager`` now has support for seeing exposed methods via
  ``dir``, allowing `IPython`_ tab completion to be useful. Merge of GH-104,
  fixes GH-55.

- Add pickle support for models using ``FieldTracker``.  Thanks Ondrej Slintak
  for the report.  Thanks Matthew Schinckel for the fix.  Merge of GH-130,
  fixes GH-83.

.. _IPython: http://ipython.org/


2.0.3 (2014.03.19)
-------------------

- Fix ``get_query_set`` vs ``get_queryset`` in ``PassThroughManager`` for
  Django <1.6. Fixes issues with related managers not filtering by relation
  properly. Thanks whop, Bojan Mihelac, Daniel Shapiro, and Matthew Schinckel
  for the report; Matthew for the fix. Merge of GH-121.

- Fix ``FieldTracker`` with deferred model attributes. Thanks Michael van
  Tellingen. Merge of GH-115.

- Fix ``InheritanceManager`` with self-referential FK; avoid infinite
  recursion. Thanks rsenkbeil. Merge of GH-114.

2.0.2 (2014.02.19)
-------------------

- ASCII-fold all non-ASCII characters in changelog. Apologies to those whose
  names are mangled by this change. It seems that distutils makes it impossible
  to handle non-ASCII content reliably under Python 3 in a setup.py
  long_description, when the system encoding may be ASCII. Thanks Simone Dalla
  for the report. Fixes GH-113.


2.0.1 (2014.02.11)
-------------------

- Fix dependency to be on "Django" rather than "django", which plays better
  with static PyPI mirrors. Thanks Travis Swicegood.

- Fix issue with attempt to access ``__slots__`` when copying
  ``PassThroughManager``. Thanks Patryk Zawadzki. Merge of GH-105.

- Improve ``InheritanceManager`` so any attributes added by using extra(select)
  will be propagated onto children. Thanks Curtis Maloney. Merge of GH-101,
  fixes GH-34.

- Added ``InheritanceManagerMixin``, ``InheritanceQuerySetMixin``,
  ``PassThroughManagerMixin``, and ``QueryManagerMixin`` to allow composing
  their functionality with other custom manager/queryset subclasses (e.g. those
  in GeoDjango). Thanks Douglas Meehan!


2.0 (2014.01.06)
----------------

- BACKWARDS-INCOMPATIBLE: Indexing into a ``Choices`` instance now translates
  database representations to human-readable choice names, rather than simply
  indexing into an array of choice tuples. (Indexing into ``Choices`` was
  previously not documented.) If you have code that is relying on indexing or
  slicing ``Choices``, the simplest workaround is to change e.g. ``STATUS[1:]``
  to ``list(STATUS)[1:]``.

- Fixed bug with checking for field name conflicts for added query managers on
  `StatusModel`.

- Can pass `choices_name` to `StatusField` to use a different name for
  choices class attribute. ``STATUS`` is used by default.

- Can pass model subclasses, rather than strings, into
  `select_subclasses()`. Thanks Keryn Knight. Merge of GH-79.

- Deepcopying a `Choices` instance no longer fails with infinite recursion in
  `getattr`. Thanks Leden. Merge of GH-75.

- `get_subclass()` method is now available on both managers and
  querysets. Thanks Travis Swicegood. Merge of GH-82.

- Fix bug in `InheritanceManager` with grandchild classes on Django 1.6+;
  `select_subclasses('child', 'child__grandchild')` would only ever get to the
  child class. Thanks Keryn Knight for report and proposed fix.

- MonitorField now accepts a 'when' parameter. It will update only when the field
  changes to one of the values specified.


1.5.0 (2013.08.29)
------------------

- `Choices` now accepts option-groupings. Fixes GH-14.

- `Choices` can now be added to other `Choices` or to any iterable, and can be
  compared for equality with itself. Thanks Tony Aldridge. (Merge of GH-76.)

- `Choices` now `__contains__` its Python identifier values. Thanks Keryn
  Knight. (Merge of GH-69).

- Fixed a bug causing ``KeyError`` when saving with the parameter
  ``update_fields`` in which there are untracked fields. Thanks Mikhail
  Silonov. (Merge of GH-70, fixes GH-71).

- Fixed ``FieldTracker`` usage on inherited models.  Fixes GH-57.

- Added mutable field support to ``FieldTracker`` (Merge of GH-73, fixes GH-74)


1.4.0 (2013.06.03)
------------------

- Introduced ``FieldTracker`` as replacement for ``ModelTracker``, which is now
  deprecated.

- ``PassThroughManager.for_queryset_class()`` no longer ignores superclass
  ``get_query_set``. Thanks Andy Freeland.

- Fixed ``InheritanceManager`` bug with grandchildren in Django 1.6. Thanks
  CrazyCasta.

- Fixed lack of ``get_FOO_display`` method for ``StatusField``. Fixes GH-41.


1.3.1 (2013.04.11)
------------------

- Added explicit default to ``BooleanField`` in tests, for Django trunk
  compatibility.

- Fixed intermittent ``StatusField`` bug.  Fixes GH-29.

- Added Python 3 support.

- Dropped support for Django 1.2 and 1.3.  Django 1.4.2+ required.


1.3.0 (2013.03.27)
------------------

- Allow specifying default value for a ``StatusField``. Thanks Felipe
  Prenholato.

- Fix calling ``create()`` on a ``RelatedManager`` that subclasses a dynamic
  ``PassThroughManager``. Thanks SeiryuZ for the report. Fixes GH-24.

- Add workaround for https://code.djangoproject.com/ticket/16855 in
  InheritanceQuerySet to avoid overriding prior calls to
  ``select_related()``. Thanks ivirabyan.

- Added support for arbitrary levels of model inheritance in
  InheritanceManager. Thanks ivirabyan. (This feature only works in Django
  1.6+ due to https://code.djangoproject.com/ticket/16572).

- Added ``ModelTracker`` for tracking field changes between model saves. Thanks
  Trey Hunner.


1.2.0 (2013.01.27)
------------------

- Moved primary development from `Bitbucket`_ to `GitHub`_. Bitbucket mirror
  will continue to receive updates; Bitbucket issue tracker will be closed once
  all issues tracked in it are resolved.

.. _BitBucket: https://bitbucket.org/carljm/django-model-utils/overview
.. _GitHub: https://github.com/carljm/django-model-utils/

- Removed deprecated ``ChoiceEnum``, ``InheritanceCastModel``,
  ``InheritanceCastManager``, and ``manager_from``.

- Fixed pickling of ``PassThroughManager``. Thanks Rinat Shigapov.

- Set ``use_for_related_fields = True`` on ``QueryManager``.

- Added ``__len__`` method to ``Choices``. Thanks Ryan Kaskel and James Oakley.

- Fixed ``InheritanceQuerySet`` on Django 1.5. Thanks Javier Garcia Sogo.

1.1.0 (2012.04.13)
------------------

- Updated AutoCreatedField, AutoLastModifiedField, MonitorField, and
  TimeFramedModel to use ``django.utils.timezone.now`` on Django 1.4.
  Thanks Donald Stufft.

- Fixed annotation of InheritanceQuerysets. Thanks Jeff Elmore and Facundo
  Gaich.

- Dropped support for Python 2.5 and Django 1.1. Both are no longer supported
  even for security fixes, and should not be used.

- Added ``PassThroughManager.for_queryset_class()``, which fixes use of
  ``PassThroughManager`` with related fields. Thanks Ryan Kaskel for report and
  fix.

- Added ``InheritanceManager.get_subclass()``. Thanks smacker.

1.0.0 (2011.06.16)
------------------

- Fixed using SplitField on an abstract base model.

- Fixed issue #8, adding ``use_for_related_fields = True`` to
  ``InheritanceManager``.

- Added ``PassThroughManager``. Thanks Paul McLanahan.

- Added pending-deprecation warnings for ``InheritanceCastModel``,
  ``manager_from``, and Django 1.1 support. Removed documentation for the
  deprecated utilities. Bumped ``ChoiceEnum`` from pending-deprecation to
  deprecation.

- Fixed issue #6, bug with InheritanceManager and descriptor fields (e.g.
  FileField).  Thanks zyegfryed for the fix and sayane for tests.

0.6.0 (2011.02.18)
------------------

- updated SplitField to define get_prep_value rather than get_db_prep_value.
  This avoids deprecation warnings on Django trunk/1.3, but makes SplitField
  incompatible with Django versions prior to 1.2.

- added InheritanceManager, a better approach to selecting subclass instances
  for Django 1.2+. Thanks Jeff Elmore.

- added InheritanceCastManager and InheritanceCastQuerySet, to allow bulk
  casting of a queryset to child types.  Thanks Gregor Muellegger.

0.5.0 (2010.09.24)
------------------

- added manager_from (thanks George Sakkis)
- added StatusField, MonitorField, TimeFramedModel, and StatusModel
  (thanks Jannis Leidel)
- deprecated ChoiceEnum and replaced with Choices

0.4.0 (2010.03.16)
------------------

- added SplitField
- added ChoiceEnum
- added South support for custom model fields

0.3.0
-----

- Added ``QueryManager``
