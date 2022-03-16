# encoding: utf-8

import json
import logging

import ckan.model as model
import ckantoolkit as tk
from ckantoolkit import _, abort, c, g, get_action, get_validator, \
    request, render, Invalid, NotAuthorized, ObjectNotFound

from ckanext.ytp_comments.request_helpers import RequestHelper
import constants
import helpers
from .reporting.helpers import export_helpers, helpers as reporting_helpers

log = logging.getLogger(__name__)

DATAREQUEST_OPEN_MAX_DAYS = constants.DATAREQUEST_OPEN_MAX_DAYS
COMMENT_NO_REPLY_MAX_DAYS = constants.COMMENT_NO_REPLY_MAX_DAYS


def _get_errors_summary(errors):
    errors_summary = ''

    for key, error in errors.items():
        errors_summary = ', '.join(error)

    return errors_summary


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': g.user, 'auth_user_obj': helpers.get_user()}


def open_datarequest(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic initialization
    c.datarequest = {}
    try:
        tk.check_access(constants.OPEN_DATAREQUEST, context, data_dict)
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

        if c.datarequest.get('closed', False) is False:
            return tk.abort(403, _('This data request is already open'))
        else:
            data_dict = {}
            data_dict['id'] = id
            data_dict['organization_id'] = c.datarequest.get('organization_id')

            tk.get_action(constants.OPEN_DATAREQUEST)(context, data_dict)
            tk.redirect_to(
                tk.url_for('datarequest.show', id=data_dict['id']))
    except tk.ValidationError as e:
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return tk.abort(403, errors_summary)
    except tk.ObjectNotFound as e:
        log.warn(e)
        return tk.abort(404, _('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        return tk.abort(403, _('You are not authorized to open the Data Request %s' % id))


def show_schema(dataset_id, resource_id):
    data_dict = {'id': resource_id}
    context = _get_context()

    try:
        tk.check_access(constants.RESOURCE_SHOW, context, data_dict)
        resource = tk.get_action(constants.RESOURCE_SHOW)(context, data_dict)
        schema_data = resource.get('schema')
        c.schema_data = json.dumps(schema_data, indent=2, sort_keys=True)
        return tk.render('schema/show.html')
    except tk.ObjectNotFound as e:
        log.warn(e)
        return tk.abort(404, _('Resource %s not found') % resource_id)
    except tk.NotAuthorized as e:
        log.warn(e)
        return tk.abort(403, _('You are not authorized to view the Data Scheme for the resource %s' % resource_id))


def _valid_report_type(report_type):
    if report_type not in constants.REPORT_TYPES:
        msg = _('Report type {0} not valid').format(report_type)
        log.warn(msg)
        return abort(404, msg)


def _get_report_type_permission(report_type):
    return 'admin' if report_type == constants.REPORT_TYPE_ADMIN else 'create_dataset'


def reporting_index():
    request_helper = RequestHelper(request)
    org_id = request_helper.get_first_query_param('organisation')
    report_type = request_helper.get_first_query_param('report_type', '')

    try:
        report_permission = _get_report_type_permission(report_type)
        helpers.check_user_access(report_permission)

        extra_vars = {
            'user_dict': helpers.get_user().as_dict(),
        }

        if report_type:
            error = _valid_report_type(report_type)
            if error:
                return error

            organisations = reporting_helpers.get_organisation_list(report_permission)

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
                    start_date, end_date = reporting_helpers.get_report_date_range(request)
                    extra_vars.update({
                        'start_date': start_date,
                        'end_date': end_date,
                        'metrics': reporting_helpers.gather_engagement_metrics(org_id, start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS),
                        'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                        'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
                    })
                elif report_type == constants.REPORT_TYPE_ADMIN:
                    extra_vars.update({
                        'metrics': reporting_helpers.gather_admin_metrics(org_id, report_permission)
                    })

        return render(
            'reporting/index.html',
            extra_vars=extra_vars
        )
    except ObjectNotFound as e:  # Exception raised from get_action('organization_show')
        log.warn(e)
        return abort(404, _('Organisation %s not found') % org_id)
    except NotAuthorized as e:  # Exception raised from check_user_access
        log.warn(e)
        organisation = request_helper.get_first_query_param('organisation')
        if organisation:
            msg = 'You are not authorised to view the {0} report for organisation {1}'.format(report_type, organisation)
        else:
            msg = 'You are not authorised to view the {0} report'.format(report_type)

        return abort(403, _(msg))


def export_reports():
    report_type = RequestHelper(request).get_first_query_param('report_type', '')
    try:
        report_permission = _get_report_type_permission(report_type)
        helpers.check_user_access(report_permission)
        error = _valid_report_type(report_type)
        if error:
            return error

        if report_type == constants.REPORT_TYPE_ENGAGEMENT:
            return _export_engagement_report(report_type, report_permission)
        elif report_type == constants.REPORT_TYPE_ADMIN:
            return _export_admin_report(report_type, report_permission)
    except NotAuthorized as e:  # Exception raised from check_user_access
        log.warn(e)
        return abort(403, _('You are not authorised to export the {0} report'.format(report_type)))


def _export_engagement_report(report_type, report_permission):
    start_date, end_date = reporting_helpers.get_report_date_range(request)

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


def _export_admin_report(report_type, report_permission):
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


def datasets(org_id, metric):
    report_type = RequestHelper(request).get_first_query_param('report_type', '')
    try:
        report_permission = _get_report_type_permission(report_type)
        reporting_helpers.check_user_org_access(org_id, report_permission)
        error = _valid_report_type(report_type)
        if error:
            return error

        get_validator('group_id_exists')(org_id, reporting_helpers.get_context())

        org = get_action('organization_show')({}, {'id': org_id})

        data_dict = {
            'org_id': org_id,
            'org_title': org['title'],
            'metric': metric,
            'user_dict': helpers.get_user().as_dict(),
            'report_type': report_type
        }

        if metric == 'no-reply':

            start_date, end_date = reporting_helpers.get_report_date_range(request)

            utc_start_date, \
                utc_end_date, \
                utc_reply_expected_by_date = reporting_helpers.get_utc_dates(
                    start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS)

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
        return abort(404, _('Organisation %s not found') % org_id)
    except NotAuthorized as e:  # Exception raised from check_user_access
        log.warn(e)
        return abort(403, _('You are not authorised to view the dataset {0} report for organisation {1}'.format(report_type, org_id)))


def datarequests(org_id, metric):
    """Displays a list of data requests for the given organisation based on the desired metric"""
    request_helper = RequestHelper(request)
    report_type = request_helper.get_first_query_param('report_type', '')
    try:
        report_permission = _get_report_type_permission(report_type)
        reporting_helpers.check_user_org_access(org_id, report_permission)
        error = _valid_report_type(report_type)
        if error:
            return error

        get_validator('group_id_exists')(org_id, reporting_helpers.get_context())

        start_date, end_date = reporting_helpers.get_report_date_range(request)

        utc_start_date, \
            utc_end_date, \
            utc_reply_expected_by_date, \
            utc_expected_closure_date = reporting_helpers.get_utc_dates(
                start_date, end_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS)

        circumstance = request_helper.get_first_query_param('circumstance')

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
            'user_dict': helpers.get_user().as_dict(),
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
            closing_circumstances = [x['circumstance'] for x in reporting_helpers.get_closing_circumstance_list()]

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
        return abort(404, _('Organisation %s not found') % org_id)
    except NotAuthorized as e:  # Exception raised from check_user_access
        log.warn(e)
        return abort(403, _('You are not authorised to view the datarequest {0} report for organisation {1}'.format(report_type, org_id)))
