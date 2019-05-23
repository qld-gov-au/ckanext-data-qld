# ckanext-data-qld
A custom CKAN extension for Data.Qld

## Installation

1. Clone this repository

2. Activate python virtualenv and install extension:

        . /usr/lib/ckan/default/bin/activate
        cd /usr/lib/ckan/default/src/ckanext-data-qld
        python setup.py develop

3. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld data_qld_googleanalytics

4. Restart web server(s), e.g.

        sudo service apache restart
        sudo service nginx restart


---------------
Config Settings
---------------

# ckanext-data_qld_googleanalytics
ckan.data_qld_googleanalytics.id = UA-1010101-1
ckan.data_qld_googleanalytics.collection_url = http://www.google-analytics.com/collect
# Dictionary of api actions to capture to send to google analytics.
# Key is the api_action name
# Value is the event_label sent to google analytics with the {0} replaced with the query parameter value eg. package_id. resource_id, query values
ckan.data_qld_googleanalytics.capture_api_actions = {"package_show": "package_show | Package ID: {0}"}