#!/usr/bin/env sh
##
# Initialise CKAN instance.
#
set -e

if [ "$VENV_DIR" != "" ]; then
  . ${VENV_DIR}/bin/activate
fi
CLICK_ARGS="--yes" ckan_cli db clean
ckan_cli db init
ckan_cli db upgrade
ckan_cli datastore set-permissions | psql "postgresql://ckan:ckan@postgres-datastore/ckan?sslmode=disable" --set ON_ERROR_STOP=1

# Initialise validation tables
PASTER_PLUGIN=ckanext-validation ckan_cli validation init-db

# Initialise the Comments database tables
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli comments initdb
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli comments updatedb
PASTER_PLUGIN=ckanext-ytp-comments ckan_cli comments init_notifications_db

# Initialise the archiver database tables
PASTER_PLUGIN=ckanext-archiver ckan_cli archiver init

# Initialise the reporting database tables
PASTER_PLUGIN=ckanext-report ckan_cli report initdb

# Initialise the QA database tables
PASTER_PLUGIN=ckanext-qa ckan_cli qa init

# Create some base test data
. $APP_DIR/scripts/create-test-data.sh
