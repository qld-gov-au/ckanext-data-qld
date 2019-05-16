#!/usr/bin/env sh
##
# Install current extension.
#
set -e

CKAN_ROOT="${CKAN_ROOT:-/app/ckan/default}"

. "${CKAN_ROOT}/bin/activate"

pip install -r "/app/requirements.txt"
python setup.py develop

deactivate
