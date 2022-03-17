# ckanext-data-qld

A custom CKAN extension for Data.Qld

[![Tests](https://github.com/qld-gov-au/ckanext-data-qld/actions/workflows/test.yml/badge.svg)](https://github.com/qld-gov-au/ckanext-data-qld/actions/workflows/test.yml)

[![CircleCI](https://circleci.com/gh/qld-gov-au/ckanext-data-qld/tree/develop.svg?style=shield)](https://circleci.com/gh/qld-gov-au/ckanext-data-qld/tree/develop)

## Local environment setup
- Make sure that you have latest versions of all required software installed:
  - [Docker](https://www.docker.com/)
  - [Pygmy](https://pygmy.readthedocs.io/)
  - [Ahoy](https://github.com/ahoy-cli/ahoy)
- Make sure that all local web development services are shut down (Apache/Nginx, Mysql, MAMP etc).
- Checkout project repository (in one of the [supported Docker directories](https://docs.docker.com/docker-for-mac/osxfs/#access-control)).
- `pygmy up`
- `ahoy build`
- You may need to use sudo on linux

Building on Ubuntu (optional: behind proxy)
- composer from compose
  - sudo pip install docker-compose
- sudo apt-get install composer
- ensure /etc/gemrc has the following
  ``http_proxy: http://localhost:3128
    https_proxy: http://localhost:3128``
- if squid proxy is in use on your machine ensure that ``acl localnet src 172.17.0.0/16``  #  allows your public ip for loopback
- https://docs.docker.com/network/proxy/
  ~/.docker/config.json
  ``
{
 "proxies":
  {
  "default":
   {
     "httpProxy": "http://hostexternalip:3128",
     "httpsProxy": "http://hostexternalip:3128",
     "noProxy": ""
   }
  }
}
``
  - https://docs.docker.com/config/daemon/systemd/
    sudo mkdir -p /etc/systemd/system/docker.service.d
    sudo vi /etc/systemd/system/docker.service.d/http-proxy.conf
    ``[Service]
      Environment="HTTP_PROXY=http://localhost:3128/"``
    sudo vi /etc/systemd/system/docker.service.d/https-proxy.conf
    ``[Service]
      Environment="HTTPS_PROXY=http://localhost:3128/"``
    sudo systemctl daemon-reload
    sudo systemctl restart docker


Use `admin`/`password` to login to CKAN.

## Available `ahoy` commands
Run each command as `ahoy <command>`.
  ```
   build        Build or rebuild project.
   clean        Remove containers and all build files.
   cli          Start a shell inside CLI container or run a command.
   doctor       Find problems with current project setup.
   down         Stop Docker containers and remove container, images, volumes and networks.
   flush-redis  Flush Redis cache.
   info         Print information about this project.
   install-site Install a site.
   lint         Lint code.
   logs         Show Docker logs.
   pull         Pull latest docker images.
   reset        Reset environment: remove containers, all build, manually created and Drupal-Dev files.
   restart      Restart all stopped and running Docker containers.
   start        Start existing Docker containers.
   stop         Stop running Docker containers.
   test-bdd     Run BDD tests.
   test-unit    Run unit tests.
   up           Build and start Docker containers.
  ```

## Coding standards
Python code linting uses [flake8](https://github.com/PyCQA/flake8) with configuration captured in `.flake8` file.

Set `ALLOW_LINT_FAIL=1` in `.env` to allow lint failures.

## Nose tests
`ahoy test-unit`

Set `ALLOW_UNIT_FAIL=1` in `.env` to allow unit test failures.

## Behavioral tests
`ahoy test-bdd`

Set `ALLOW_BDD_FAIL=1` in `.env` to allow BDD test failures.

### How it works
We are using [Behave](https://github.com/behave/behave) BDD _framework_ with additional _step definitions_ provided by [Behaving](https://github.com/ggozad/behaving) library.

Custom steps described in `test/features/steps/steps.py`.

Test scenarios located in `test/features/*.feature` files.

Test environment configuration is located in `test/features/environment.py` and is setup to connect to a remote Chrome
instance running in a separate Docker container.

During the test, Behaving passes connection information to [Splinter](https://github.com/cobrateam/splinter) which
instantiates WebDriver object and establishes connection with Chrome instance. All further communications with Chrome
are handled through this driver, but in a developer-friendly way.

For a list of supported step-definitions, see https://github.com/ggozad/behaving#behavingweb-supported-matcherssteps.

## Automated builds (Continuous Integration)
In software engineering, continuous integration (CI) is the practice of merging all developer working copies to a shared mainline several times a day.
Before feature changes can be merged into a shared mainline, a complete build must run and pass all tests on CI server.

This project uses [GitHub Actions](https://github.com/features/actions) as a CI server: it imports production backups into fully built codebase and runs code linting and tests. When tests pass, a deployment process is triggered for nominated branches (usually, `master` and `develop`).

## Installation

1. Clone this repository

2. Activate python virtualenv and install extension:

        . /usr/lib/ckan/default/bin/activate
        cd /usr/lib/ckan/default/src/ckanext-data-qld
        python setup.py develop

3. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld

# data_qld_google_analytics
A custom CKAN extension for Data.Qld for sending API requests to Google Analytics

## Setup

1. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld_google_analytics

2. Add the config settings to relevant CKAN `.ini` file

        # ckanext-data_qld_googleanalytics
        ckan.data_qld_googleanalytics.id = UA-1010101-1 # Relevant Google analytics ID
        ckan.data_qld_googleanalytics.collection_url = http://www.google-analytics.com/collect

3. The file capture_api_actions.json is a dictionary of api actions to capture to send to google analytics

a. The dictionary key is the name of the api_action from https://docs.ckan.org/en/2.8/api/index.html#action-api-reference
b. The dictionary value is the event_label sent to google analytics with the {0} replaced with the query parameter value eg. package_id, resource_id, query values, sql query

4. Restart web server(s), e.g.

        sudo service apache reload
        sudo service nginx reload

# Migrating Legacy Extra Fields
*Note: The following assumes that a dump of production data has been imported into the CKAN database and any necessary database schema updates have been performed (ref.: https://docs.ckan.org/en/2.8/maintaining/database-management.html#upgrading).*

Previously, the "Security classification" and "Used in data-driven application" fields had been added as free extras to datasets, e.g.



These fields are now part of the dataset schema via the `scheming` extension (ref.: https://github.com/qld-gov-au/ckanext-data-qld/blob/develop/ckanext/data_qld/ckan_dataset.json)

The legacy field values need to be migrated to their schema counterparts.

The `ckanext-data-qld` extension contains a paster command for doing this (ref.: https://github.com/qld-gov-au/ckanext-data-qld/blob/develop/ckanext/data_qld/commands.py)

*Note: This paster command was designed to be run once for initial migration of legacy extra fields, so isn't idempotent.
If migration command is run multiple times there should not be any issues, but it is not recommended to be used again once the site is live*

To run the command:

1. Enable the python virtual environment:

        . /usr/lib/ckan/default/bin/activate

2. Run the following command:

        paster --plugin=ckanext-data-qld migrate_extras -c /path/to/ini_file.ini

3. Rebuild the Solr index:

        paster --plugin=ckan search-index rebuild -c /PATH/TO/YOUR_INI_FILE.ini

This will iterate through each of the datasets in CKAN and copy the *"Security classification"* and *"Used in data-driven application"* extra field values to the dataset schema fields security_classification and data_driven_application respectively.

# Demoting Publishers to Editor role
*Note: The following assumes that a dump of production data has been imported into the CKAN database and any necessary database schema updates have been performed (ref.: https://docs.ckan.org/en/2.8/maintaining/database-management.html#upgrading).*

There is a paster command to set the role for any users with names starting with `publisher-` from admin to editor where necessary.

*Note: This paster command was designed to be run once. If run multiple times there should not be any issues, as it will not re-assign users who are already assigned the editor role - but it is not designed to be idempotent*

To run the command:

1. Enable the python virtual environment:

        . /usr/lib/ckan/default/bin/activate

2. Run the following command:

        paster --plugin=ckanext-data-qld demote_publishers -c /etc/ckan/default/development.ini

# Data.Qld Engagement Reporting Plugin

## Configuration

1. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld_reporting

 2. Add the following optional config settings to relevant CKAN `.ini` file, if desired:

        # ckanext-data_qld_reporting
        ckan.reporting.datarequest_open_max_days = 60 # Defaults to 60
        ckan.reporting.comment_no_reply_max_days = 10 # Defaults to 10
        ckan.reporting.engagement_json_config = PATH_TO_FILE # Defaults to os.path.dirname(os.path.realpath(__file__)) + '/../engagement_report_csv.json'
        ckan.reporting.admin_json_config = PATH_TO_FILE # Defaults to os.path.dirname(os.path.realpath(__file__)) + '/../admin_report_csv.json'

