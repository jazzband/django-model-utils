CHANGES
=======

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

