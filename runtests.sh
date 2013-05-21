#!/bin/sh

coverage erase
tox
coverage html
