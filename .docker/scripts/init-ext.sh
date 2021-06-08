#!/usr/bin/env sh
##
# Install current extension.
#
set -e

PIP="${APP_DIR}/bin/pip"
cd $WORKDIR
$PIP install -r "requirements.txt"
$PIP install -r "requirements-dev.txt"
$APP_DIR/bin/python setup.py develop

# Validate that the extension was installed correctly.
if ! $PIP list | grep ckanext-data-qld-theme > /dev/null; then echo "Unable to find the extension in the list"; exit 1; fi

