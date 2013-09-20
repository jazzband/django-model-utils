CHANGES
=======

master (unreleased)
-------------------

* Fix bug in `InheritanceManager` with grandchild classes on Django 1.6+;
  `select_subclasses('child', 'child__grandchild')` would only ever get to the
  child class. Thanks Keryn Knight for report and proposed fix.


1.5.0 (2013.08.29)
------------------

* `Choices` now accepts option-groupings. Fixes GH-14.

* `Choices` can now be added to other `Choices` or to any iterable, and can be
  compared for equality with itself. Thanks Tony Aldridge. (Merge of GH-76.)

* `Choices` now `__contains__` its Python identifier values. Thanks Keryn
  Knight. (Merge of GH-69).

* Fixed a bug causing ``KeyError`` when saving with the parameter
  ``update_fields`` in which there are untracked fields. Thanks Mikhail
  Silonov. (Merge of GH-70, fixes GH-71).

* Fixed ``FieldTracker`` usage on inherited models.  Fixes GH-57.

* Added mutable field support to ``FieldTracker`` (Merge of GH-73, fixes GH-74)


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

- Fixed ``InheritanceQuerySet`` on Django 1.5. Thanks Javier García Sogo.

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
  casting of a queryset to child types.  Thanks Gregor Müllegger.

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

* Added ``QueryManager``

