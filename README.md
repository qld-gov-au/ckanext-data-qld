# ckanext-data-qld
A custom CKAN extension for Data.Qld

## Installation

1. Clone this repository

2. Activate python virtualenv and install extension:

        . /usr/lib/ckan/default/bin/activate
        cd /usr/lib/ckan/default/src/ckanext-data-qld
        python setup.py develop

3. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld 

4. Restart web server(s), e.g.

        sudo service apache restart
        sudo service nginx restart


# data_qld_google_analytics
A custom CKAN extension for Data.Qld for sending API requests to Google Analytics

## Setup

1. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld_google_analytics 

2. Add the config settings to relevantCKAN `.ini` file 
        # ckanext-data_qld_googleanalytics
        ckan.data_qld_googleanalytics.id = UA-1010101-1 # Relevant Google analytics ID
        ckan.data_qld_googleanalytics.collection_url = http://www.google-analytics.com/collect

3. The file capture_api_actions.json is a dictionary of api actions to capture to send to google analytics 
        a. The dictionary key is the name of the api_action from https://docs.ckan.org/en/2.8/api/index.html#action-api-reference
        b. The dictionary value is the event_label sent to google analytics with the {0} replaced with the query parameter value eg. package_id. resource_id, query values


