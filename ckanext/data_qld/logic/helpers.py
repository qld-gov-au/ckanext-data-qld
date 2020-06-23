import datetime
import calendar
import ckan.model as model
import ckan.plugins.toolkit as toolkit
import logging

get_action = toolkit.get_action
log = logging.getLogger(__name__)


def check_org_access(org_id):
    toolkit.check_access('organization_update', get_context(), {'organization_id': org_id})


def get_organization_name(org_id):
    org = get_action('organization_show')({}, {'id': org_id})

    log.debug(org)

    return org['title']


def get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
        'auth_user_obj': toolkit.c.userobj
    }


def get_year_month(year, month):
    now = datetime.datetime.now()

    if not year:
        year = now.year

    if not month:
        month = now.month

    return int(year), int(month)


def get_report_date_range(year, month):
    month_range = calendar.monthrange(year, month)

    start_date = datetime.datetime(year, month, 1).isoformat()
    end_date = datetime.datetime(year, month, month_range[1], 23, 59, 59).isoformat()

    return start_date, end_date


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


def get_data_request_metrics(org_id, max_days):
    # Compile as much info as we can from the one query
    closed = 0
    open = 0
    open_plus_max_days = 0
    total = 0

    circumstances = {
        'No circumstance': {
            'accepted_dataset': {'count': 0, 'average': 0, 'data': []},
            'no_accepted_dataset': {'count': 0, 'average': 0, 'data': []}
        }
    }

    for data_request in get_action('datarequests')({}, org_id):

        total += 1

        if data_request.close_time:
            closed += 1

            # @TODO: Handle data requests with No closing circumstance
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


def gather_metrics(org_id, start_date, comment_no_reply_max_days, datarequest_open_max_days):
    return {
        'organization_followers': get_action('organization_follower_count')({}, {'id': org_id}),
        'dataset_followers': get_action('dataset_followers')({}, org_id),
        'dataset_comments': get_action('dataset_comments')({}, org_id),
        'dataset_comment_followers': get_action('dataset_comment_followers')({}, org_id),
        'datasets_min_one_comment_follower': get_action('datasets_min_one_comment_follower')({}, org_id),
        'datasets_no_replies_after_x_days': get_action('datasets_no_replies_after_x_days')(
            {},
            {
                'org_id': org_id,
                'start_date': start_date,
                'max_days': comment_no_reply_max_days
            }
        ),
        'datarequests': get_data_request_metrics(org_id, datarequest_open_max_days),
        'datarequest_comments': get_action('datarequest_comments')({}, org_id),
        'datarequests_min_one_comment_follower': get_action('datarequests_min_one_comment_follower')({}, org_id),
        'datarequests_no_replies_after_x_days': get_action('datarequests_no_replies_after_x_days')(
            {},
            {
                'org_id': org_id,
                'start_date': start_date
            }
        ),
        'open_datarequests_no_comments_after_x_days': get_action('open_datarequests_no_comments_after_x_days')({}, org_id),
    }
