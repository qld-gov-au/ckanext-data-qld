import logging
import ckanext.data_qld.auth_functions as auth_functions
import ckan.plugins.toolkit as toolkit

from ckan.lib.base import BaseController, render
from ckan.plugins.toolkit import get_action, request
from ckanext.data_qld.logic import helpers
from ckanext.data_qld.logic import export_helpers

log = logging.getLogger(__name__)

# @TODO: Reset this to 60
DATAREQUEST_OPEN_MAX_DAYS = 10
# @TODO: Reset this to 10
COMMENT_NO_REPLY_MAX_DAYS = 5


class ReportingController(BaseController):

    @classmethod
    def check_user_access(cls):
        context = helpers.get_context()
        data_dict = {'permission': 'create_dataset'}
        toolkit.check_access('has_user_permission_for_some_org', context, data_dict)

    def index(self):
        self.check_user_access()

        start_date, end_date = helpers.get_report_date_range(request.GET.get('start_date', None), request.GET.get('end_date', None))
        org_id = request.GET.get('organisation', None)
        extra_vars = {}

        if org_id:
            org = get_action('organization_show')({}, {'id': org_id})

            extra_vars = {
                'org_id': org_id,
                'org_name': org['title'],
                'start_date': start_date,
                'end_date': end_date,
                'metrics': helpers.gather_metrics(org_id, start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS),
                'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
            }

        return render(
            'reporting/index.html',
            extra_vars=extra_vars
        )

    def export(self):
        import csv
        from pylons import response

        self.check_user_access()

        start_date, end_date = helpers.get_report_date_range(request.GET.get('start_date', None), request.GET.get('end_date', None))

        report_config = export_helpers.get_report_config()

        row_order, row_properties = export_helpers.get_row_order_and_properties(report_config)

        csv_header_row = ['']

        dict_csv_rows = {}

        for key in row_properties:
            dict_csv_rows[key] = []

        closing_circumstances = [c['circumstance'] for c in helpers.get_closing_circumstance_list()]

        for circumstance in closing_circumstances:
            key = 'Closed data requests - %s' % circumstance
            row_order.append(key)
            dict_csv_rows[key] = []

        # Gather all the metrics for each organisation
        for organization in helpers.get_organisation_list_for_user('create_dataset'):
            export_helpers.add_org_metrics_to_report(
                organization,
                start_date,
                end_date,
                csv_header_row,
                row_properties,
                dict_csv_rows,
                closing_circumstances,
                COMMENT_NO_REPLY_MAX_DAYS,
                DATAREQUEST_OPEN_MAX_DAYS
            )

        return export_helpers.output_report_csv(csv_header_row, row_order, dict_csv_rows)

    def datasets(self, org_id, metric):

        # @TODO: Validation
        self.check_user_access()
        start_date, end_date = helpers.get_report_date_range(request.GET.get('start_date', None), request.GET.get('end_date', None))

        if metric == 'no-reply':
            datasets = get_action('datasets_no_replies_after_x_days')(
                    {},
                    {
                        'org_id': org_id,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                )

        return render(
            'reporting/datasets.html',
            extra_vars={
                'org_id': org_id,
                'datasets': datasets,
                'metric': metric,
            }
        )

    def datarequests(self, org_id, metric):
        """Displays a list of data requests for the given organisation based on the desired metric"""

        # @TODO: Regex org_id against ([a-f0-9\-)
        self.check_user_access() 
        
        start_date, end_date = helpers.get_report_date_range(request.GET.get('start_date', None), request.GET.get('end_date', None))
        data_dict = {
            'org_id': org_id,
            'start_date': start_date,
            'end_date': end_date,
            'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
            'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
        }
        circumstance = None

        if metric == 'no-reply':
            datarequests = get_action('datarequests_no_replies_after_x_days')({}, data_dict)
        elif metric == 'no-comments':
            datarequests = get_action('open_datarequests_no_comments_after_x_days')({}, data_dict)
        elif metric == 'open-max-days':
            datarequests = get_action('datarequests_open_after_x_days')({}, data_dict)
        else:
            circumstance = request.GET.get('circumstance', None)
            data_dict['circumstance'] = circumstance
            closing_circumstances = [c['circumstance'] for c in helpers.get_closing_circumstance_list()]

            if circumstance not in closing_circumstances:
                raise toolkit.Invalid(toolkit._('Circumstance {0} is not valid'.format(circumstance)))

            datarequests = get_action('datarequests_for_circumstance')({}, data_dict)

        return render(
            'reporting/datarequests.html',
            extra_vars={
                'org_id': org_id,
                'datarequests': datarequests,
                'metric': metric,
                'circumstance': circumstance
            }
        )
