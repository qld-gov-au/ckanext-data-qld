#!/usr/bin/env sh
##
# Initialise CKAN instance.
#
set -e

CKAN_USER_NAME="${CKAN_USER_NAME:-admin}"
CKAN_USER_PASSWORD="${CKAN_USER_PASSWORD:-password}"
CKAN_USER_EMAIL="${CKAN_USER_EMAIL:-admin@localhost}"

. /app/ckan/default/bin/activate \
  && cd /app/ckan/default/src/ckan \
  && paster db clean -c /app/ckan/default/production.ini \
  && paster db init -c /app/ckan/default/production.ini \
  && paster --plugin=ckan user add "${CKAN_USER_NAME}" email="${CKAN_USER_EMAIL}" password="${CKAN_USER_PASSWORD}" -c /app/ckan/default/production.ini \
  && paster --plugin=ckan sysadmin add "${CKAN_USER_NAME}" -c /app/ckan/default/production.ini

# # Initialise the ckanext-report tables
paster --plugin=ckanext-report report initdb -c /app/ckan/default/production.ini

# Initialise the ckanext-archiver tables
paster --plugin=ckanext-archiver archiver init -c /app/ckan/default/production.ini

# Initialise the ckanext-qa tables
paster --plugin=ckanext-qa qa init -c /app/ckan/default/production.ini

# Initialise the Comments database tables
paster --plugin=ckanext-ytp-comments initdb --config=/app/ckan/default/production.ini
paster --plugin=ckanext-ytp-comments updatedb --c /app/ckan/default/production.ini
paster --plugin=ckanext-ytp-comments init_notifications_db --c /app/ckan/default/production.ini

# Create some base test data
. /app/scripts/create-test-data.sh
