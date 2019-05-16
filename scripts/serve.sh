#!/usr/bin/env sh
set -e

dockerize -wait tcp://postgres:5432 -timeout 1m
dockerize -wait tcp://solr:8983 -timeout 1m

. /app/ckan/default/bin/activate \
    && paster serve /app/ckan/default/production.ini
