# encoding: utf-8
from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='ckanext-data-qld',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='1.3.2',

    description='Custom extension for Data QLD',
    long_description='',

    # The project's main homepage.
    url='https://github.com/qld-gov-au/ckanext-data-qld',

    # Author details
    author='Queensland Government and Salsa Digital',
    author_email='',

    # Choose your license
    license='AGPL',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='CKAN',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    namespace_packages=['ckanext'],

    install_requires=[
        # CKAN extensions should not list dependencies here, but in a separate
        # ``requirements.txt`` file.
        #
        # http://docs.ckan.org/en/latest/extensions/best-practices.html#add-third-party-libraries-to-requirements-txt
    ],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    include_package_data=True,
    package_data={},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points='''
        [ckan.plugins]
        data_qld=ckanext.data_qld.plugin:DataQldPlugin
        data_qld_integration=ckanext.data_qld.plugin:DataQldPlugin
        data_qld_resources=ckanext.data_qld.plugin:PlaceholderPlugin
        data_qld_google_analytics=ckanext.data_qld.google_analytics.plugin:GoogleAnalyticsPlugin
        data_qld_reporting=ckanext.data_qld.plugin:PlaceholderPlugin

        data_qld_test=ckanext.data_qld.test_plugin:DataQldTestPlugin

        [paste.paster_command]
        migrate_extras = ckanext.data_qld.commands:MigrateExtras
        demote_publishers = ckanext.data_qld.commands:DemotePublishers
        update_fullname = ckanext.data_qld.user_creation.commands:UpdateFullname
        send_email_dataset_due_to_publishing_notification = ckanext.data_qld.resource_freshness.commands:SendEmailDatasetDueToPublishingNotification
        send_email_dataset_overdue_notification = ckanext.data_qld.resource_freshness.commands:SendEmailDatasetOverdueNotification
        update_missing_values = ckanext.data_qld.commands:MissingValues


        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
    ''',

    # If you are changing from the default layout of your extension, you may
    # have to change the message extractors, you can read more about babel
    # message extraction at
    # http://babel.pocoo.org/docs/messages/#extraction-method-mapping-and-configuration
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
)
