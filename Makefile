all: init docs test

init:
	python setup.py develop
	pip install tox coverage Sphinx

test:
	coverage erase
	tox
	coverage html

docs: documentation

documentation:
	python setup.py build_sphinx
