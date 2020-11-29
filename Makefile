VIRTUALENV = virtualenv --python=python3
PYTHON = $(VENV)/bin/python
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
INSTALL_STAMP = $(VENV)/.install.stamp

all: init docs test

init: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON) setup.py
	$(VENV)/bin/pip install -e .
	$(VENV)/bin/pip install tox coverage Sphinx
	touch $(INSTALL_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

test: init
	$(VENV)/bin/coverage erase
	$(VENV)/bin/tox
	$(VENV)/bin/coverage html

docs: documentation

documentation: init
	$(PYTHON) setup.py build_sphinx

messages: init
	$(PYTHON) translations.py make

compilemessages: init
	$(PYTHON) translations.py compile

format:
	isort model_utils tests setup.py
