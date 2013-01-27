CHANGES
=======

tip (unreleased)
----------------

- Moved primary development from `Bitbucket`_ to `GitHub`_. Bitbucket mirror
  will continue to receive updates; Bitbucket issue tracker will be closed once
  all issues tracked in it are resolved.

.. _BitBucket: https://bitbucket.org/carljm/django-model-utils/overview
.. _GitHub: https://github.com/carljm/django-model-utils/

- Removed deprecated ``ChoiceEnum`` class.

- Added ``UpdateOrCreateMixin`` for custom queryset subclasses. Thanks Antti
  Kaihola.

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

