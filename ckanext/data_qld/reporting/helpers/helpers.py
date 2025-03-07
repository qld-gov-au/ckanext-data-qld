# encoding: utf-8

import logging
import pytz
from datetime import datetime, timedelta

import ckantoolkit as tk
from ckan import model

from ckanext.data_qld import helpers
from ckanext.data_qld.reporting.constants import (
    REPORT_DEIDENTIFIED_NO_SCHEMA_COUNT_FROM
)


log = logging.getLogger(__name__)


def check_user_access(permission, context=None):
    data_dict = {
        'permission': permission
    }
    tk.check_access(
        'has_user_permission_for_some_org',
        context if context else get_context(),
        data_dict
    )


def check_user_org_access(org_ids, permission='create_dataset', context=None):
    if not context:
        context = get_context()
    if not isinstance(org_ids, list):
        org_ids = [org_ids]
    for org_id in org_ids:
        data_dict = {
            'org_id': org_id,
            'permission': permission
        }
        tk.check_access(
            'has_user_permission_for_org',
            context,
            data_dict
        )


def get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': get_username(),
        'auth_user_obj': helpers.get_user()
    }


def get_username():
    # 'g' is not a regular data structure so we can't use 'hasattr'
    if 'user' in dir(tk.g):
        return tk.g.user
    elif tk.current_user:
        # CKAN is moving toward replacing 'g.user' with 'current_user'
        return tk.current_user.name
    else:
        return None


def get_report_date_range(request):
    request_helper = helpers.RequestHelper(request)
    start_date = request_helper.get_first_query_param('start_date')
    end_date = request_helper.get_first_query_param('end_date')

    if start_date:
        start_date = tk.h.date_str_to_datetime(start_date)
    else:
        start_date = datetime(2019, 7, 10)

    if end_date:
        end_date = tk.h.date_str_to_datetime(end_date)
    else:
        # This end_date will get passed into the method `get_utc_dates` which is expecting a ckan_timezone date to be converted into utc
        ckan_timezone = tk.config.get('ckan.display_timezone', None)
        end_date = datetime.now(pytz.timezone(ckan_timezone))

    return start_date.date().isoformat(), end_date.date().isoformat()


def get_closing_circumstance_list():
    circumstances = []
    if tk.asbool(tk.config.get('ckan.datarequests.enable_closing_circumstances', False)):
        from ckanext.datarequests import helpers
        circumstances = helpers.get_closing_circumstances()
    return circumstances


def get_average_closing_days(circumstance_data):
    total_days = 0

    for row in circumstance_data['data']:
        total_days += row['days']

    return int(total_days / circumstance_data['count'])


def get_data_request_metrics(data_dict):
    """Compile as much info as we can from the one query"""
    closed = open = open_plus_max_days = total = total_close_days = 0

    max_days = data_dict.get('datarequest_open_max_days', None)

    circumstances = {}

    no_circumstance = {
        'accepted_dataset': {'data': []},
        'no_accepted_dataset': {'data': []}
    }

    def append_data(target, data_request, days):
        target['data'].append({
            'id': data_request.id,
            'open_time': data_request.open_time,
            'close_time': data_request.close_time,
            'days': days
        })

    for data_request in tk.get_action('datarequests')({}, data_dict):
        total += 1

        if data_request.close_time:
            closed += 1
            delta = data_request.close_time - data_request.open_time
            days = int(delta.total_seconds() / 86400)
            total_close_days += days

            circumstance = data_request.close_circumstance

            if circumstance:
                if circumstance not in circumstances.keys():
                    circumstances[circumstance] = {'data': []}
                append_data(circumstances[circumstance], data_request, days)
            else:
                if data_request.accepted_dataset_id:
                    append_data(
                        no_circumstance['accepted_dataset'], data_request, days)
                else:
                    append_data(
                        no_circumstance['no_accepted_dataset'], data_request, days)
        else:
            open += 1
            days = delta_in_days(datetime.utcnow(), data_request.open_time)
            open_plus_max_days += 1 if days > max_days else 0

    for c in circumstances:
        circumstances[c]['count'] = len(circumstances[c]['data'])
        if circumstances[c]['count'] > 0:
            circumstances[c]['average'] = get_average_closing_days(
                circumstances[c])

    for n in no_circumstance:
        no_circumstance[n]['count'] = len(no_circumstance[n]['data'])
        if no_circumstance[n]['count'] > 0:
            no_circumstance[n]['average'] = get_average_closing_days(
                no_circumstance[n])

    data_requests = {
        'total': total,
        'open': open,
        'open_plus_max_days': open_plus_max_days,
        'closed': closed,
        'circumstances': circumstances,
        'no_circumstance': no_circumstance,
        'average_overall': int(total_close_days / closed) if total_close_days > 0 else 0
    }

    return data_requests


def delta_in_days(latest_date, earliest_date):
    delta = latest_date - earliest_date

    return int(delta.total_seconds() / 86400)


def get_utc_dates(start_date, end_date, comment_no_reply_max_days=None, datarequest_open_max_days=None):
    """Process textual date representations"""
    date_format = '%Y-%m-%d %H:%M:%S'

    timezone = pytz.timezone("UTC")
    local_timezone = pytz.timezone(tk.config.get('ckan.display_timezone'))

    # Always consider `start_date` and `end_date` as local dates
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

    # Make the local datetimes timezone aware
    tz_start_datetime = local_timezone.localize(start_datetime)
    tz_end_datetime = local_timezone.localize(end_datetime)

    utc_start_datetime = tz_start_datetime.astimezone(timezone)
    utc_end_datetime = tz_end_datetime.astimezone(timezone)

    if comment_no_reply_max_days:
        utc_reply_expected_by_date = utc_end_datetime - \
            timedelta(days=comment_no_reply_max_days)

    if datarequest_open_max_days:
        utc_expected_closure_date = utc_end_datetime - \
            timedelta(days=datarequest_open_max_days)

    utc_start_datetime = utc_start_datetime.strftime(date_format)
    utc_end_datetime = utc_end_datetime.strftime(date_format)

    if comment_no_reply_max_days and datarequest_open_max_days:
        return utc_start_datetime, \
            utc_end_datetime, \
            utc_reply_expected_by_date, \
            utc_expected_closure_date
    elif comment_no_reply_max_days:
        return utc_start_datetime, \
            utc_end_datetime, \
            utc_reply_expected_by_date
    elif datarequest_open_max_days:
        return utc_start_datetime, \
            utc_end_datetime, \
            utc_expected_closure_date
    else:
        return utc_start_datetime, \
            utc_end_datetime


def gather_engagement_metrics(org_id, start_date, end_date, comment_no_reply_max_days, datarequest_open_max_days):
    """Collect engagement statistics metrics for the provided organisation"""
    utc_start_date, \
        utc_end_date, \
        utc_reply_expected_by_date, \
        utc_expected_closure_date = get_utc_dates(start_date,
                                                  end_date,
                                                  comment_no_reply_max_days,
                                                  datarequest_open_max_days
                                                  )

    data_dict = {
        'org_id': org_id,
        'start_date': start_date,
        'end_date': end_date,
        'comment_no_reply_max_days': comment_no_reply_max_days,
        'datarequest_open_max_days': datarequest_open_max_days,
        'utc_start_date': utc_start_date,
        'utc_end_date': utc_end_date,
        'utc_reply_expected_by_date': utc_reply_expected_by_date,
        'utc_expected_closure_date': utc_expected_closure_date,
    }

    return {
        'organisation_followers': tk.get_action('organisation_followers')({}, data_dict),
        'dataset_followers': tk.get_action('dataset_followers')({}, data_dict),
        'dataset_comments': tk.get_action('dataset_comments')({}, data_dict),
        'dataset_comment_followers': tk.get_action('dataset_comment_followers')({}, data_dict),
        'datasets_min_one_comment_follower': tk.get_action('datasets_min_one_comment_follower')({}, data_dict),
        'dataset_comments_no_replies_after_x_days': tk.get_action('dataset_comments_no_replies_after_x_days')({},
                                                                                                              data_dict),
        'datarequests': get_data_request_metrics(data_dict),
        'datarequest_comments': tk.get_action('datarequest_comments')({}, data_dict),
        'datarequests_min_one_comment_follower': tk.get_action('datarequests_min_one_comment_follower')({}, data_dict),
        'datarequests_no_replies_after_x_days': tk.get_action('datarequests_no_replies_after_x_days')({}, data_dict),
        'open_datarequests_no_comments_after_x_days': tk.get_action('open_datarequests_no_comments_after_x_days')({},
                                                                                                                  data_dict),
    }


def gather_admin_metrics(org_id, permission):
    """Collect admin statistics metrics for the provided organisation"""

    # get the current authentication info for our API calls
    context = {'auth_user_obj': tk.current_user, 'user': tk.current_user.name}

    data_dict = {
        'org_id': org_id,
        'return_count_only': True,
        'permission': permission
    }

    de_identified_datasets = tk.get_action('de_identified_datasets')(context, data_dict)
    de_identified_datasets_no_schema = tk.get_action('de_identified_datasets_no_schema')(context, data_dict)
    overdue_datasets = tk.get_action('overdue_datasets')(context, data_dict)
    datasets_no_groups = tk.get_action('datasets_no_groups')(context, data_dict)
    datasets_no_tags = tk.get_action('datasets_no_tags')(context, data_dict)
    pending_privacy_assessment = tk.get_action('resources_pending_privacy_assessment')(context, data_dict)

    if isinstance(org_id, list):
        metrics = {}
        for org in org_id:
            metrics[org] = {
                'de_identified_datasets': 0,
                'de_identified_datasets_no_schema': 0,
                'overdue_datasets': 0,
                'datasets_no_groups': 0,
                'datasets_no_tags': 0,
                'pending_privacy_assessment': 0,
            }

        def _add_metric(metric_list, key):
            for row in metric_list:
                metrics[row[0]][key] = row[1]

        _add_metric(de_identified_datasets, 'de_identified_datasets')
        _add_metric(de_identified_datasets_no_schema, 'de_identified_datasets_no_schema')
        _add_metric(overdue_datasets, 'overdue_datasets')
        _add_metric(datasets_no_groups, 'datasets_no_groups')
        _add_metric(datasets_no_tags, 'datasets_no_tags')
        _add_metric(pending_privacy_assessment, 'pending_privacy_assessment')
    else:
        metrics = {
            'de_identified_datasets': de_identified_datasets,
            'de_identified_datasets_no_schema': de_identified_datasets_no_schema,
            'overdue_datasets': overdue_datasets,
            'datasets_no_groups': datasets_no_groups,
            'datasets_no_tags': datasets_no_tags,
            'pending_privacy_assessment': pending_privacy_assessment,
        }
    return metrics


def get_organisation_list(permission):
    organisations = []
    for user_organisation in get_organisation_list_for_user(permission):
        organisations.append({'value': user_organisation.get(
            'id'), 'text': user_organisation.get('display_name')})

    return organisations


def get_organisation_list_for_user(permission):
    try:
        return tk.get_action('organization_list_for_user')(get_context(), {'permission': permission})
    except Exception as e:
        log.error(
            '*** Failed to retrieve organization_list_for_user {0}'.format(get_username()))
        log.error(e)
        return []


def get_deidentified_count_from_date():
    return tk.config.get(
        REPORT_DEIDENTIFIED_NO_SCHEMA_COUNT_FROM, "2022-11-01"
    )


def get_deidentified_count_from_date_display():
    count_from = get_deidentified_count_from_date()
    return tk.h.date_str_to_datetime(count_from).strftime("%d %B %Y")
