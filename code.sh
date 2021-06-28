#!/usr/bin/env bash

pip install autoflake yapf isort black autopep8
autopep8 --verbose --in-place --recursive --aggressive --aggressive --ignore=W605 .
autoflake --in-place --recursive --remove-all-unused-imports --remove-unused-variables --ignore-init-module-imports .
black .
isort .
yapf --style='{based_on_style: google, spaces_before_comment: 2, split_before_logical_operator: true, column_limit=90}' -ir .