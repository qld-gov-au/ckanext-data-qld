#!/usr/bin/env sh
##
# Initialise CKAN data for testing.
#
set -e

. "${APP_DIR}"/bin/activate
CLICK_ARGS="--yes" ckan_cli db clean
ckan_cli db init
ckan_cli datastore set-permissions | psql "postgresql://datastore_write:pass@postgres-datastore/datastore_test" --set ON_ERROR_STOP=1

# Initialise validation tables
ckan_cli validation init-db

# Initialise the Comments database tables
ckan_cli comments initdb
ckan_cli comments init_notifications_db

# Initialise the archiver database tables
ckan_cli archiver init

# Initialise the reporting database tables
ckan_cli report initdb

# Initialise the QA database tables
ckan_cli qa init

# Initialise the data request tables if applicable
if (ckan_cli datarequests --help); then
    # Click 7+ expects hyphenated action names,
    # older Click expects underscore.
    if (ckan_cli datarequests init-db --help); then
        ckan_cli datarequests init-db
    else
        ckan_cli datarequests init_db
    fi
fi
