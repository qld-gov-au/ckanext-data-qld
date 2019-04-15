# ckanext-data-qld-theme
A custom CKAN theme extension for Data.Qld

## Installation

1. Clone this repository

2. Activate python virtualenv and install extension:

        . /usr/lib/ckan/default/bin/activate
        cd /usr/lib/ckan/default/src/ckanext-data-qld-theme
        python setup.py develop

3. Add the extension to the relevant CKAN `.ini` file `plugins` definition:

        ckan.plugins = ... data_qld_theme

4. Restart web server(s), e.g.

        sudo service apache restart
        sudo service nginx restart
