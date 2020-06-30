import logging
import ckan.plugins.toolkit as toolkit

from ckan.lib.base import BaseController
from ckanext.data_qld.reporting import constants
from ckanext.data_qld.reporting.helpers import export_helpers, helpers

log = logging.getLogger(__name__)
get_action = toolkit.get_action
request = toolkit.request
render = toolkit.render
get_validator = toolkit.get_validator
ObjectNotFound = toolkit.ObjectNotFound
Invalid = toolkit.Invalid
NotAuthorized = toolkit.NotAuthorized
abort = toolkit.abort
_ = toolkit._
DATAREQUEST_OPEN_MAX_DAYS = constants.DATAREQUEST_OPEN_MAX_DAYS
COMMENT_NO_REPLY_MAX_DAYS = constants.COMMENT_NO_REPLY_MAX_DAYS


class ReportingController(BaseController):

    @classmethod
    def check_user_access(cls):
        toolkit.check_access(
            'has_user_permission_for_some_org',
            helpers.get_context(), {'permission': 'create_dataset'}
        )

    def index(self):
        try:
            self.check_user_access()

            start_date, end_date = helpers.get_report_date_range(request)
            org_id = request.GET.get('organisation', None)

            organisations = helpers.get_organisation_list()

            if organisations and len(organisations) == 1:
                org_id = organisations[0]['value']

            extra_vars = {
                'organisations': organisations,
                'user_dict': get_action('user_show')({}, {'id': toolkit.c.userobj.id})
            }

            if org_id:
                org = get_action('organization_show')({}, {'id': org_id})

                extra_vars.update({
                    'org_id': org_id,
                    'org_title': org['title'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'metrics': helpers.gather_metrics(org_id, start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS),
                    'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                    'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
                })

            return render(
                'reporting/index.html',
                extra_vars=extra_vars
            )
        except ObjectNotFound as e:  # Exception raised from get_action('organization_show')
            log.warn(e)
            abort(404, _('Organisation %s not found') % org_id)
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            msg = 'You are not authorised to view the report for organisation %s' % request.GET.get('organisation', None) \
                if request.GET.get('organisation', None) else 'You are not authorised to view the report'
            abort(403, _(msg))

    def export(self):
        try:
            self.check_user_access()

            start_date, end_date = helpers.get_report_date_range(request)

            report_config = export_helpers.csv_report_config()

            row_order, row_properties = export_helpers.csv_row_order_and_properties(report_config)

            csv_header_row = ['']

            dict_csv_rows = {}

            for key in row_properties:
                dict_csv_rows[key] = []

            # This is to allow for closing circumstances to be configurable through the CKAN UI
            closing_circumstances = [c['circumstance'] for c in helpers.get_closing_circumstance_list()]

            no_closing_circumstances = ['accepted_dataset', 'no_accepted_dataset']

            for circumstance in closing_circumstances:
                key = 'Closed data requests - %s' % circumstance
                row_order.append(key)
                dict_csv_rows[key] = []

            # Data requests without closing circumstance, i.e. those prior to ~July 2020
            for no_circumstance in no_closing_circumstances:
                key = 'Closed data requests - Closed %s' % no_circumstance.replace('_', ' ')
                row_order.append(key)
                dict_csv_rows[key] = []

            # Add the average closing time column for each circumstance
            for circumstance in closing_circumstances:
                key = 'Average days closed data request - %s' % circumstance
                row_order.append(key)
                dict_csv_rows[key] = []

            # Add the average closing time column for each closure without circumstance
            for no_circumstance in no_closing_circumstances:
                key = 'Average days closed data request - Closed %s' % no_circumstance.replace('_', ' ')
                row_order.append(key)
                dict_csv_rows[key] = []

            # Gather all the metrics for each organisation
            for organisation in helpers.get_organisation_list_for_user('create_dataset'):
                export_helpers.csv_add_org_metrics(
                    organisation,
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
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            abort(403, _('You are not authorised to export the report'))

    def datasets(self, org_id, metric):
        try:
            self.check_user_access()
            get_validator('group_id_exists')(org_id, helpers.get_context())

            start_date, end_date = helpers.get_report_date_range(request)

            start_date, end_date, reply_expected_by_date = helpers.process_dates(start_date,
                                                                                 end_date,
                                                                                 COMMENT_NO_REPLY_MAX_DAYS
                                                                                 )

            org = get_action('organization_show')({}, {'id': org_id})

            if metric == 'no-reply':
                comments = get_action('dataset_comments_no_replies_after_x_days')(
                    {},
                    {
                        'org_id': org_id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'reply_expected_by_date': reply_expected_by_date
                    }
                )
                # Action `dataset_comments_no_replies_after_x_days` returns a collection of comments with no replies
                # On this page we only need to display distinct datasets containing those comments
                datasets = []
                comment_ids = {}
                for comment in comments:
                    if comment.package_name in comment_ids:
                        comment_ids[comment.package_name].append(comment.comment_id)
                    else:
                        comment_ids[comment.package_name] = [comment.comment_id]
                        datasets.append(comment)

            return render(
                'reporting/datasets.html',
                extra_vars={
                    'org_id': org_id,
                    'org_title': org['title'],
                    'start_date': start_date,
                    'end_date': end_date,
                    'datasets': datasets,
                    'metric': metric,
                    'total_comments': len(comments),
                    'comment_ids': comment_ids,
                    'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                    'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS,
                    'user_dict': get_action('user_show')({}, {'id': toolkit.c.userobj.id})
                }
            )
        except Invalid as e:  # Exception raised from get_validator('group_id_exists')
            log.warn(e)
            abort(404, _('Organisation %s not found') % org_id)
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            abort(403, _('You are not authorised to view the dataset report for organisation %s' % org_id))

    def datarequests(self, org_id, metric):
        """Displays a list of data requests for the given organisation based on the desired metric"""
        try:
            self.check_user_access()
            get_validator('group_id_exists')(org_id, helpers.get_context())

            start_date, end_date = helpers.get_report_date_range(request)

            start_date, \
                end_date, \
                reply_expected_by_date, \
                expected_closure_date = helpers.process_dates(start_date,
                                                              end_date,
                                                              COMMENT_NO_REPLY_MAX_DAYS,
                                                              DATAREQUEST_OPEN_MAX_DAYS
                                                              )

            circumstance = request.GET.get('circumstance', None)

            org = get_action('organization_show')({}, {'id': org_id})

            data_dict = {
                'org_id': org_id,
                'org_title': org['title'],
                'start_date': start_date,
                'end_date': end_date,
                'metric': metric,
                'circumstance': circumstance,
                'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS,
                'reply_expected_by_date': reply_expected_by_date,
                'expected_closure_date': expected_closure_date,
                'user_dict': get_action('user_show')({}, {'id': toolkit.c.userobj.id})
            }

            if metric == 'no-reply':
                datarequests_comments = get_action('datarequests_no_replies_after_x_days')({}, data_dict)
                # Action `datarequests_no_replies_after_x_days` returns a collection of comments with no replies
                # On this page we only need to display distinct datarequests containing those comments
                distinct_datarequests = []
                comment_ids = {}
                for datarequest in datarequests_comments:
                    if datarequest.datarequest_id in comment_ids:
                        comment_ids[datarequest.datarequest_id].append(datarequest.comment_id)
                    else:
                        comment_ids[datarequest.datarequest_id] = [datarequest.comment_id]
                        distinct_datarequests.append(datarequest)

                datarequests = distinct_datarequests
                data_dict.update(
                    {
                        'total_comments': len(datarequests_comments),
                        'comment_ids': comment_ids
                    }
                )
            elif metric == 'no-comments':
                datarequests = get_action('open_datarequests_no_comments_after_x_days')({}, data_dict)
            elif metric == 'open-max-days':
                datarequests = get_action('datarequests_open_after_x_days')({}, data_dict)
            else:
                closing_circumstances = [c['circumstance'] for c in helpers.get_closing_circumstance_list()]

                if circumstance not in closing_circumstances:
                    raise Invalid(_('Circumstance {0} is not valid'.format(circumstance)))

                datarequests = get_action('datarequests_for_circumstance')({}, data_dict)

            data_dict['datarequests'] = datarequests

            return render(
                'reporting/datarequests.html',
                extra_vars=data_dict
            )
        except Invalid as e:  # Exception raised from get_validator('group_id_exists')
            log.warn(e)
            abort(404, _('Organisation %s not found') % org_id)
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            abort(403, _('You are not authorised to view the datarequest report for organisation %s' % org_id))
