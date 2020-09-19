Contributing
============

.. image:: https://jazzband.co/static/img/jazzband.svg
   :target: https://jazzband.co/
   :alt: Jazzband

This is a `Jazzband <https://jazzband.co>`_ project. By contributing you agree
to abide by the `Contributor Code of Conduct
<https://jazzband.co/about/conduct>`_ and follow the `guidelines
<https://jazzband.co/about/guidelines>`_.

Below is a list of tips for submitting issues and pull requests.

Submitting Issues
-----------------

Issues are easier to reproduce/resolve when they have:

- A pull request with a failing test demonstrating the issue
- A code example that produces the issue consistently
- A traceback (when applicable)


Pull Requests
-------------

When creating a pull request:

- Write tests
- Note user-facing changes in the `CHANGES`_ file
- Update the documentation
- Add yourself to the `AUTHORS`_ file
- If you have added or changed translated strings, run ``make messages`` to
  update the ``.po`` translation files, and update translations for any
  languages you know. Then run ``make compilemessages`` to compile the ``.mo``
  files. If your pull request leaves some translations incomplete, please
  mention that in the pull request and commit message.

.. _AUTHORS: AUTHORS.rst
.. _CHANGES: CHANGES.rst


Translations
------------

If you are able to provide translations for a new language or to update an
existing translation file, make sure to run makemessages beforehand::

    python django-admin makemessages -l ISO_LANGUAGE_CODE

This command will collect all translation strings from the source directory
and create or update the translation file for the given language. Now open the
translation file (.po) with a text-editor and start editing.
After you finished editing add yourself to the list of translators.
If you have created a new translation, make sure to copy the header from one
of the existing translation files.


Testing
-------

Please add tests for your code and ensure existing tests don't break.  To run
the tests against your code::

    python setup.py test

Please use tox to test the code against supported Python and Django versions.
First install tox::

    pip install tox coverage

To run tox and generate a coverage report (in ``htmlcov`` directory)::

    make test

**Please note**: Before a pull request can be merged, all tests must pass and
code/branch coverage in tests must be 100%.
