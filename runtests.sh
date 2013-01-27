#!/bin/sh

coverage erase
tox
coverage html --include=model_utils/* --omit=model_utils/tests/*
