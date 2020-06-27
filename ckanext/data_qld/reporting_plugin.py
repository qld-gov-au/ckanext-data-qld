import ckan.plugins as plugins
import logic.action.get as get
import auth_functions as auth

from ckanext.data_qld.logic import helpers


class ReportingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IAuthFunctions)

    # IActions
    def get_actions(self):
        actions = {
            'organisation_followers': get.organisation_followers,
            'dataset_followers': get.dataset_followers,
            'dataset_comments': get.dataset_comments,
            'dataset_comment_followers': get.dataset_comment_followers,
            'datasets_min_one_comment_follower': get.datasets_min_one_comment_follower,
            'datarequests_min_one_comment_follower': get.datarequests_min_one_comment_follower,
            'datarequests': get.datarequests,
            'datarequest_comments': get.datarequest_comments,
            'dataset_comments_no_replies_after_x_days': get.dataset_comments_no_replies_after_x_days,
            'datarequests_no_replies_after_x_days': get.datarequests_no_replies_after_x_days,
            'datarequests_for_circumstance': get.datarequests_for_circumstance,
            'open_datarequests_no_comments_after_x_days': get.open_datarequests_no_comments_after_x_days,
            'datarequests_open_after_x_days': get.datarequests_open_after_x_days,
            'comments_no_replies_after_x_days': get.comments_no_replies_after_x_days,
        }
        return actions

    # IRoutes

    def before_map(self, map):
        map.connect('/dashboard/reporting/export',
                    controller='ckanext.data_qld.controllers.reporting:ReportingController',
                    action='export')
        map.connect('dashboard.reports', '/dashboard/reporting',
                    controller='ckanext.data_qld.controllers.reporting:ReportingController',
                    action='index')
        map.connect('/dashboard/reporting/datasets/{org_id}/{metric}',
                    controller='ckanext.data_qld.controllers.reporting:ReportingController',
                    action='datasets')
        map.connect('/dashboard/reporting/datarequests/{org_id}/{metric}',
                    controller='ckanext.data_qld.controllers.reporting:ReportingController',
                    action='datarequests')
        return map

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_closing_circumstance_list': helpers.get_closing_circumstance_list,
            'get_organisation_list': helpers.get_organisation_list
        }

        # IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            'has_user_permission_for_some_org': auth.has_user_permission_for_some_org,
            'has_user_permission_for_org': auth.has_user_permission_for_org
        }
        return auth_functions
