#!/usr/bin/env sh
set -e

sed -i 's@ckan.site_url.*@ckan.site_url = http://'"$LOCALDEV_URL"'@g' /app/ckan/default/production.ini

dockerize -wait tcp://postgres:5432 -timeout 1m
dockerize -wait tcp://solr:8983 -timeout 1m

. /app/ckan/default/bin/activate \
    && paster serve /app/ckan/default/production.ini
