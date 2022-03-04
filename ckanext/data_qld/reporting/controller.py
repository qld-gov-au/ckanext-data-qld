import logging

from ckantoolkit import \
    _, abort, BaseController, get_action, get_validator, request, render, \
    Invalid, NotAuthorized, ObjectNotFound
from ckanext.data_qld import helpers as data_qld_helpers
from ckanext.data_qld.reporting import constants
from ckanext.data_qld.reporting.helpers import export_helpers, helpers

log = logging.getLogger(__name__)

DATAREQUEST_OPEN_MAX_DAYS = constants.DATAREQUEST_OPEN_MAX_DAYS
COMMENT_NO_REPLY_MAX_DAYS = constants.COMMENT_NO_REPLY_MAX_DAYS


class ReportingController(BaseController):

    def valid_report_type(self, report_type):
        if report_type not in constants.REPORT_TYPES:
            msg = _('Report type {0} not valid').format(report_type)
            log.warn(msg)
            abort(404, msg)

    def get_report_type_permission(self, report_type):
        return 'admin' if report_type == constants.REPORT_TYPE_ADMIN else 'create_dataset'

    def index(self):
        org_id = request.GET.get('organisation', None)
        report_type = request.GET.get('report_type', '')

        try:
            report_permission = self.get_report_type_permission(report_type)
            helpers.check_user_access(report_permission)

            extra_vars = {
                'user_dict': data_qld_helpers.get_user().as_dict(),
            }

            if report_type:
                self.valid_report_type(report_type)

                organisations = helpers.get_organisation_list(report_permission)

                extra_vars.update({
                    'organisations': organisations,
                    'report_type': report_type
                })

                if organisations and len(organisations) == 1:
                    org_id = organisations[0]['value']

                if org_id:
                    org = get_action('organization_show')({}, {'id': org_id})

                    extra_vars.update({
                        'org_id': org_id,
                        'org_title': org['title'],
                    })

                    if report_type == constants.REPORT_TYPE_ENGAGEMENT:
                        start_date, end_date = helpers.get_report_date_range(request)
                        extra_vars.update({
                            'start_date': start_date,
                            'end_date': end_date,
                            'metrics': helpers.gather_engagement_metrics(org_id, start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS),
                            'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                            'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
                        })
                    elif report_type == constants.REPORT_TYPE_ADMIN:
                        extra_vars.update({
                            'metrics': helpers.gather_admin_metrics(org_id, report_permission)
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
            if request.GET.get('organisation'):
                msg = 'You are not authorised to view the {0} report for organisation {1}'.format(report_type, request.GET.get('organisation'))
            else:
                msg = 'You are not authorised to view the {0} report'.format(report_type)

            abort(403, _(msg))

    def export(self):
        report_type = request.GET.get('report_type', '')
        try:
            report_permission = self.get_report_type_permission(report_type)
            helpers.check_user_access(report_permission)
            self.valid_report_type(report_type)

            if report_type == constants.REPORT_TYPE_ENGAGEMENT:
                return self.export_engagement_report(report_type, report_permission)
            elif report_type == constants.REPORT_TYPE_ADMIN:
                return self.export_admin_report(report_type, report_permission)
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            abort(403, _('You are not authorised to export the {0} report'.format(report_type)))

    def export_engagement_report(self, report_type, report_permission):
        start_date, end_date = helpers.get_report_date_range(request)

        report_config = export_helpers.csv_report_config(report_type)

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

        key = 'Average days closed data requests - overall'
        dict_csv_rows[key] = []
        row_order.append(key)

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
        for organisation in helpers.get_organisation_list_for_user(report_permission):
            export_helpers.engagement_csv_add_org_metrics(
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

        return export_helpers.output_report_csv(csv_header_row, row_order, dict_csv_rows, report_type)

    def export_admin_report(self, report_type, report_permission):
        report_config = export_helpers.csv_report_config(report_type)

        row_order, row_properties = export_helpers.csv_row_order_and_properties(report_config)

        csv_header_row = ['Criteria']

        dict_csv_rows = {}

        for key in row_properties:
            dict_csv_rows[key] = []

        # Gather all the metrics for each organisation
        for organisation in helpers.get_organisation_list_for_user(report_permission):
            export_helpers.admin_csv_add_org_metrics(
                organisation,
                csv_header_row,
                row_properties,
                dict_csv_rows,
                report_permission
            )

        return export_helpers.output_report_csv(csv_header_row, row_order, dict_csv_rows, report_type)

    def datasets(self, org_id, metric):
        report_type = request.GET.get('report_type', '')
        try:
            report_permission = self.get_report_type_permission(report_type)
            helpers.check_user_org_access(org_id, report_permission)
            self.valid_report_type(report_type)

            get_validator('group_id_exists')(org_id, helpers.get_context())

            org = get_action('organization_show')({}, {'id': org_id})

            data_dict = {
                'org_id': org_id,
                'org_title': org['title'],
                'metric': metric,
                'user_dict': data_qld_helpers.get_user().as_dict(),
                'report_type': report_type
            }

            if metric == 'no-reply':

                start_date, end_date = helpers.get_report_date_range(request)

                utc_start_date, \
                    utc_end_date, \
                    utc_reply_expected_by_date = helpers.get_utc_dates(start_date,
                                                                       end_date,
                                                                       COMMENT_NO_REPLY_MAX_DAYS
                                                                       )

                data_dict.update(
                    {
                        'start_date': start_date,
                        'end_date': end_date,
                        'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS,
                        'utc_start_date': utc_start_date,
                        'utc_end_date': utc_end_date,
                        'utc_reply_expected_by_date': utc_reply_expected_by_date,
                    })

                comments = get_action('dataset_comments_no_replies_after_x_days')(
                    {},
                    data_dict
                )
                # Action `dataset_comments_no_replies_after_x_days` returns a
                # collection of comments with no replies
                # On this page we only need to display distinct datasets containing those comments
                datasets = []
                comment_ids = {}
                for comment in comments:
                    if comment.package_name in comment_ids:
                        comment_ids[comment.package_name].append(comment.comment_id)
                    else:
                        comment_ids[comment.package_name] = [comment.comment_id]
                        datasets.append(comment)

                data_dict.update({
                    'datasets': datasets,
                    'total_comments': len(comments),
                    'comment_ids': comment_ids
                })
            elif metric == 'de-identified-datasets':
                data_dict.update({
                    'return_count_only': False,
                    'permission': report_permission
                })
                datasets = get_action('de_identified_datasets')({}, data_dict)
                data_dict.update({
                    'datasets': datasets
                })
            elif metric == 'overdue-datasets':
                data_dict.update({
                    'return_count_only': False,
                    'permission': report_permission
                })
                datasets = get_action('overdue_datasets')({}, data_dict)
                data_dict.update({
                    'datasets': datasets
                })

            return render(
                'reporting/datasets.html',
                extra_vars=data_dict
            )
        except Invalid as e:  # Exception raised from get_validator('group_id_exists')
            log.warn(e)
            abort(404, _('Organisation %s not found') % org_id)
        except NotAuthorized as e:  # Exception raised from check_user_access
            log.warn(e)
            abort(403, _('You are not authorised to view the dataset {0} report for organisation {1}'.format(report_type, org_id)))

    def datarequests(self, org_id, metric):
        """Displays a list of data requests for the given organisation based on the desired metric"""
        report_type = request.GET.get('report_type', '')
        try:
            report_permission = self.get_report_type_permission(report_type)
            helpers.check_user_org_access(org_id, report_permission)
            self.valid_report_type(report_type)

            get_validator('group_id_exists')(org_id, helpers.get_context())

            start_date, end_date = helpers.get_report_date_range(request)

            utc_start_date, \
                utc_end_date, \
                utc_reply_expected_by_date, \
                utc_expected_closure_date = helpers.get_utc_dates(start_date,
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
                'user_dict': data_qld_helpers.get_user().as_dict(),
                'utc_start_date': utc_start_date,
                'utc_end_date': utc_end_date,
                'utc_reply_expected_by_date': utc_reply_expected_by_date,
                'utc_expected_closure_date': utc_expected_closure_date,
                'report_type': report_type
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
                closing_circumstances = [x['circumstance'] for x in helpers.get_closing_circumstance_list()]

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
            abort(403, _('You are not authorised to view the datarequest {0} report for organisation {1}'.format(report_type, org_id)))
