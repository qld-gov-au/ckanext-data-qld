#!/usr/bin/env sh
##
# Initialise CKAN instance.
#
set -e

CKAN_ROOT="${CKAN_ROOT:-/app/ckan/default}"
CKAN_INI="${CKAN_INI:-/app/ckan/default/production.ini}"

CKAN_USER_NAME="${CKAN_USER_NAME:-admin}"
CKAN_USER_PASSWORD="${CKAN_USER_PASSWORD:-password}"
CKAN_USER_EMAIL="${CKAN_USER_EMAIL:-admin@localhost}"

. "${CKAN_ROOT}/bin/activate" \
  && cd "${CKAN_ROOT}/src/ckan" \
  && paster db init -c "${CKAN_INI}" \
  && paster --plugin=ckan user add "${CKAN_USER_NAME}" email="${CKAN_USER_EMAIL}" password="${CKAN_USER_PASSWORD}" -c "${CKAN_INI}" \
  && paster --plugin=ckan sysadmin add "${CKAN_USER_NAME}" -c "${CKAN_INI}"
