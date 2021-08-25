import ckan.plugins as plugins
import ckanext.data_qld.reporting.logic.action.get as get
import auth_functions as auth

from ckanext.data_qld.reporting.helpers import helpers
import ckanext.data_qld.currency.validation as currency_validator
import ckanext.data_qld.currency.helpers.helpers as ch


class ReportingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        plugins.toolkit.add_resource('reporting/fanstatic', 'data_qld_reporting')

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
                    controller='ckanext.data_qld.reporting.controller:ReportingController',
                    action='export')
        map.connect('dashboard.reports', '/dashboard/reporting',
                    controller='ckanext.data_qld.reporting.controller:ReportingController',
                    action='index')
        map.connect('/dashboard/reporting/datasets/{org_id}/{metric}',
                    controller='ckanext.data_qld.reporting.controller:ReportingController',
                    action='datasets')
        map.connect('/dashboard/reporting/datarequests/{org_id}/{metric}',
                    controller='ckanext.data_qld.reporting.controller:ReportingController',
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

    # IValidator
    def get_validators(self):
        return {'validate_next_due_date':
                currency_validator.validate_next_due_date}

    # # IPackageController

    # def create(self, entity):
    #     import pdb; pdb.set_trace()
    #     entity.next_update_due = ch.recalculate_due_date(entity.update_frequency)

    # def update(self, entity):
    #     import pdb; pdb.set_trace()
    #     entity.next_update_due = ch.recalculate_due_date(entity.update_frequency)
