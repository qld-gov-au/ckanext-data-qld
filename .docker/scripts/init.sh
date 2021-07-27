#!/usr/bin/env sh
##
# Initialise CKAN instance.
#
set -e

CKAN_USER_NAME="${CKAN_USER_NAME:-admin}"
CKAN_DISPLAY_NAME="${CKAN_DISPLAY_NAME:-Administrator}"
CKAN_USER_PASSWORD="${CKAN_USER_PASSWORD:-Password123!}"
CKAN_USER_EMAIL="${CKAN_USER_EMAIL:-admin@localhost}"

. ${APP_DIR}/bin/activate
ckan_cli db clean
ckan_cli db init

# Initialise validation tables
PASTER_PLUGIN=ckanext-validation ckan_cli validation init-db

# Initialise the Comments database tables
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli initdb
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli updatedb
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli init_notifications_db

# Initialise the archiver database tables
PASTER_PLUGIN=ckanext-archiver ckan_cli archiver init

# Initialise the reporting database tables
PASTER_PLUGIN=ckanext-report ckan_cli report initdb

# Initialise the QA database tables
PASTER_PLUGIN=ckanext-qa ckan_cli qa init

ckan_cli user add "${CKAN_USER_NAME}"\
 fullname="${CKAN_DISPLAY_NAME}"\
 email="${CKAN_USER_EMAIL}"\
 password="${CKAN_USER_PASSWORD}"
ckan_cli sysadmin add "${CKAN_USER_NAME}"

# Initialise the Comments database tables
paster --plugin=ckanext-ytp-comments initdb --config=/app/ckan/default/production.ini
paster --plugin=ckanext-ytp-comments updatedb --c /app/ckan/default/production.ini
paster --plugin=ckanext-ytp-comments init_notifications_db --c /app/ckan/default/production.ini

# Create some base test data
. $WORKDIR/scripts/create-test-data.sh
