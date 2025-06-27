#!/usr/bin/env bash
##
# Build site in CI.
#
set -ex

# Process Docker Compose configuration. This is used to avoid multiple
# docker-compose.yml files.
# Remove lines containing '###'.
sed -i -e "/###/d" docker-compose.yml
# Uncomment lines containing '##'.
sed -i -e "s/##//" docker-compose.yml

# Pull the latest images.
ahoy pull

PYTHON=python3
PYTHON_VERSION=py3

CKAN_GIT_VERSION=$CKAN_VERSION
CKAN_GIT_ORG=qld-gov-au
SOLR_VERSION=9

if [ "$CKAN_VERSION" = "2.11" ]; then
    CKAN_GIT_VERSION=ckan-2.11.3-qgov.1
elif [ "$CKAN_VERSION" = "2.10" ]; then
    CKAN_GIT_VERSION=ckan-2.10.7-qgov.1
    SOLR_VERSION=8
elif [ "$CKAN_VERSION" = "master" ]; then
    CKAN_GIT_ORG=ckan
fi

sed "s|{CKAN_VERSION}|$CKAN_VERSION|g" .docker/Dockerfile-template.ckan \
    | sed "s|{CKAN_GIT_VERSION}|$CKAN_GIT_VERSION|g" \
    | sed "s|{CKAN_GIT_ORG}|$CKAN_GIT_ORG|g" \
    | sed "s|{PYTHON_VERSION}|$PYTHON_VERSION|g" \
    | sed "s|{PYTHON}|$PYTHON|g" \
    > .docker/Dockerfile.ckan

export SOLR_VERSION
ahoy build
