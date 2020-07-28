#!/usr/bin/env sh
##
# Install current extension.
#
set -e

. /app/ckan/default/bin/activate

pip install -r "/app/requirements.txt"
pip install -r "/app/requirements-dev.txt"
pip install -r "/app/ckan/default/src/ckanext-validation/requirements.txt"
pip install -r "/app/ckan/default/src/ckanext-scheming/requirements.txt"
pip install -r "/app/ckan/default/src/ckanext-data-qld-theme/requirements.txt"
pip install -r "/app/ckan/default/src/ckanext-dcat/requirements.txt"
pip install -r "/app/ckan/default/src/ckanext-ytp-comments/requirements.txt"
python setup.py develop

# Validate that the extension was installed correctly.
if ! pip list | grep ckanext-data-qld > /dev/null; then echo "Unable to find the extension in the list"; exit 1; fi

deactivate
