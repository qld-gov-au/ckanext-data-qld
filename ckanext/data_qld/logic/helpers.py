import datetime
import calendar
import ckan.model as model
import ckan.plugins.toolkit as toolkit
import logging
import ckanext.data_qld.auth_functions as authz

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def check_org_access(org_id):
    context = get_context()
    data_dict = {'org_id': org_id, 'permission': 'create_dataset'}
    if not toolkit.check_access('has_user_permission_for_org', context, data_dict):
        toolkit.abort(403, toolkit._('User {0} is not authorized to create datasets for organisation {1} test'. format(user_name, org_id)))


def get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
        'auth_user_obj': toolkit.c.userobj
    }


def get_user():
    return toolkit.c.userobj


def get_username():
    return get_user().name


def get_report_date_range(start_date, end_date):
    if start_date:
        start_date = toolkit.h.date_str_to_datetime(start_date)
    else:
        start_date = datetime.datetime(2019, 6, 10)

    if end_date:
        end_date = toolkit.h.date_str_to_datetime(end_date)
    else:
        end_date = datetime.datetime.utcnow()

    return start_date.date().isoformat(), end_date.date().isoformat()


def get_closing_circumstance_list():
    circumstances = []
    if toolkit.asbool(toolkit.config.get('ckan.datarequests.enable_closing_circumstances', False)):
        from ckanext.datarequests import helpers
        circumstances = helpers.get_closing_circumstances()
    return circumstances


def get_closing_circumstance_average(circumstance_data):
    total_days = 0

    for row in circumstance_data['data']:
        total_days += row['days']

    return int(total_days / circumstance_data['count'])


def get_data_request_metrics(data_dict):
    # Compile as much info as we can from the one query
    closed = 0
    open = 0
    open_plus_max_days = 0
    total = 0
    max_days = data_dict.get('datarequest_open_max_days', None)

    circumstances = {
        'No circumstance': {
            'accepted_dataset': {'count': 0, 'average': 0, 'data': []},
            'no_accepted_dataset': {'count': 0, 'average': 0, 'data': []}
        }
    }

    for data_request in get_action('datarequests')({}, data_dict):
        total += 1

        if data_request.close_time:
            closed += 1

            # @TODO: Handle data requests with No closing circumstance
            # Even though in the UI you cannot close a datarequest without a circumstance
            close_circumstance = data_request.close_circumstance

            if close_circumstance:

                circumstance_exists = circumstances.get(close_circumstance, None)

                if not circumstance_exists:
                    circumstances[close_circumstance] = {'count': 0, 'average': 0, 'data': []}

                circumstances[close_circumstance]['count'] += 1

                timedelta = data_request.close_time - data_request.open_time

                days = int(timedelta.total_seconds() / 86400)

                circumstances[close_circumstance]['data'].append(
                    {
                        'id': data_request.id,
                        'open_time': data_request.open_time,
                        'close_time': data_request.close_time,
                        'timedelta': timedelta,
                        'total_seconds': timedelta.total_seconds(),
                        'days': days
                    }
                )
            else:
                if data_request.accepted_dataset_id:
                    circumstances['No circumstance']['accepted_dataset']['count'] += 1
                else:
                    circumstances['No circumstance']['no_accepted_dataset']['count'] += 1
        else:
            open += 1

            days = timedelta_in_days(datetime.datetime.utcnow(), data_request.open_time)

            if days > max_days:
                open_plus_max_days += 1

    for c in circumstances:
        if c != 'No circumstance' and circumstances[c]['count'] > 0:
            circumstances[c]['average'] = get_closing_circumstance_average(circumstances[c])

    data_requests = {
        'total': total,
        'open': open,
        'open_plus_max_days': open_plus_max_days,
        'closed': closed,
        'circumstances': circumstances
    }

    return data_requests


def timedelta_in_days(latest_date, earliest_date):
    timedelta = latest_date - earliest_date

    return int(timedelta.total_seconds() / 86400)


def gather_metrics(org_id, start_date, end_date, comment_no_reply_max_days, datarequest_open_max_days):
    data_dict = {
        'org_id': org_id,
        'start_date': start_date,
        'end_date': end_date,
        'comment_no_reply_max_days': comment_no_reply_max_days,
        'datarequest_open_max_days': datarequest_open_max_days
    }

    return {
        'organisation_followers': get_action('organisation_followers')({}, data_dict),
        'dataset_followers': get_action('dataset_followers')({}, data_dict),
        'dataset_comments': get_action('dataset_comments')({}, data_dict),
        'dataset_comment_followers': get_action('dataset_comment_followers')({}, data_dict),
        'datasets_min_one_comment_follower': get_action('datasets_min_one_comment_follower')({}, data_dict),
        'datasets_no_replies_after_x_days': get_action('datasets_no_replies_after_x_days')({}, data_dict),
        'datarequests': get_data_request_metrics(data_dict),
        'datarequest_comments': get_action('datarequest_comments')({}, data_dict),
        'datarequests_min_one_comment_follower': get_action('datarequests_min_one_comment_follower')({}, data_dict),
        'datarequests_no_replies_after_x_days': get_action('datarequests_no_replies_after_x_days')({}, data_dict),
        'open_datarequests_no_comments_after_x_days': get_action('open_datarequests_no_comments_after_x_days')({}, data_dict),
    }


def get_organisation_list():
    organisations = []
    for user_organisation in get_organisation_list_for_user('create_dataset'):
        organisations.append({'value': user_organisation.get('id'), 'text': user_organisation.get('display_name')})

    return organisations


def get_organisation_list_for_user(permission):
    try:
        return toolkit.get_action('organization_list_for_user')(get_context(), {'permission': permission})
    except Exception as e:
        log.error('*** Failed to retrieve organization_list_for_user {0}'.format(get_username()))
        log.error(e)
        return []
