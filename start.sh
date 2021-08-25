#!/usr/bin/env bash

cmdExists () {
    command -v "$1" >/dev/null 2>&1
}

if cmdExists poetry ; then
    echo "Checking Requirements..."
    # poetry install &> /dev/null
    poetry run python -m droid
else
    python -m droid
fi