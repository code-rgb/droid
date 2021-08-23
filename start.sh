#!/usr/bin/env bash

exists() {
    command -v "$1" >/dev/null 2>&1
}

if exists poetry ; then
    poetry install &> /dev/null
    poetry run python -m droid
else
    python -m droid
fi