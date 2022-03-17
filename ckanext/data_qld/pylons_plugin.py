# encoding: utf-8

from ckan import plugins

import constants


class MixinPlugin(plugins.SingletonPlugin):
    """ Provide functions specific to the Queensland Government Open Data portal.
    """
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes
    def before_map(self, m):
        # Re_Open a Data Request
        controller = 'ckanext.data_qld.controller:DataQldUI'
        m.connect(
            'data_qld.open_datarequest',
            '/%s/open/{id}' % constants.DATAREQUESTS_MAIN_PATH, controller=controller,
            action='open_datarequest', conditions=dict(method=['GET', 'POST']))

        m.connect(
            'data_qld.show_schema',
            '/dataset/{dataset_id}/resource/{resource_id}/%s/show/' % constants.SCHEMA_MAIN_PATH,
            controller=controller, action='show_schema', conditions=dict(method=['GET']))

        # Reporting
        controller = 'ckanext.data_qld.reporting.controller:ReportingController'
        m.connect('/dashboard/reporting/export', controller=controller, action='export')
        m.connect('data_qld_reporting.index', '/dashboard/reporting', controller=controller, action='index')
        m.connect(
            '/dashboard/reporting/datasets/{org_id}/{metric}', controller=controller, action='datasets')
        m.connect(
            '/dashboard/reporting/datarequests/{org_id}/{metric}', controller=controller, action='datarequests')

        return m
