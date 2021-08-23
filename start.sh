#!/usr/bin/env bash

if ! [ test $DYNO ] && [ command -v poetry ] &> /dev/null ; then
    poetry install &> /dev/null
fi

poetry run python -m droid