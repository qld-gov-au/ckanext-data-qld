# encoding: utf-8

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import re
import six

from ckantoolkit import g, get_action, request

from . import plugin

log = logging.getLogger('ckanext.googleanalytics')

GA_COOKIE_FORMAT = re.compile(r'\b_ga=GA\d+[.]\d+[.](\d+[.]\d+)')
GMT_PLUS_10 = timezone(timedelta(hours=10))


def _alter_sql(sql_query):
    '''Quick and dirty altering of sql to prevent injection'''
    sql_query = sql_query.lower()
    sql_query = sql_query.replace('select', 'CK_SEL')
    sql_query = sql_query.replace('insert', 'CK_INS')
    sql_query = sql_query.replace('update', 'CK_UPD')
    sql_query = sql_query.replace('upsert', 'CK_UPS')
    sql_query = sql_query.replace('declare', 'CK_DEC')
    return sql_query


def _safe_param(value: str, max_len: int) -> str:
    """
    Ensure GA param length is within limits.

    Length of event parameter value 100 characters

    The following exceptions apply:

        the page_title parameter must be 300 characters or fewer
        the page_referrer parameter must be 420 characters or fewer
        the page_location parameters must be 1,000 characters or fewer
    """

    if not value:
        return ""
    return value[:max_len]


def _split_param(value: str, base_key: str) -> dict:
    """
    Split long GA4 param values into 100-char chunks.
    First 100 chars go into the base param (e.g. 'action', 'label').
    Overflow chunks go into your custom definitions.


    https://support.google.com/analytics/answer/9267744?hl=en
    """
    params = {}
    if not value:
        return params

    # Always keep first 100 chars in base field
    params[base_key] = value[:100]

    # Remaining chunks
    chunks = [value[i:i + 100] for i in range(100, len(value), 100)]

    # Map chunks to overflow custom definitions
    if base_key == "action":
        keys = [
            "event_action_overflow_one",  # custom dimension
            "event_action_overflow_two",  # custom dimension
            "event_action_overflow_three"  # custom dimension
        ]
    elif base_key == "label":
        keys = [
            "event_label_overflow_one",  # custom dimension
            "event_label_overflow_two",  # custom dimension
            "event_label_overflow_three"  # custom dimension
        ]
    else:
        keys = []

    for key, chunk in zip(keys, chunks):
        params[key] = chunk

    return params


def make_daily_client_id() -> str:
    # Get IP (prefer X-Forwarded-For if present)
    ip = request.environ.get("HTTP_X_FORWARDED_FOR")
    if ip:
        ip = ip.split(",")[0].strip()
    else:
        ip = request.environ.get("REMOTE_ADDR", "0.0.0.0")

    # Get User-Agent
    ua = request.environ.get("HTTP_USER_AGENT", "missing")

    # Mix IP + UA
    identity_str = f"{ip}|{ua}"

    # Hash into a stable int
    id_hash = int(hashlib.md5(identity_str.encode()).hexdigest(), 16) % 2147483647

    day_timestamp = getStartOfDayInt()

    return f"{id_hash}.{day_timestamp}"


def getStartOfDayInt():
    now_local = datetime.now(GMT_PLUS_10)
    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(start_of_day.timestamp())


def getStartOfHourInt():
    now_local = datetime.now(GMT_PLUS_10)
    start_of_hour = now_local.replace(minute=0, second=0, microsecond=0)
    return int(start_of_hour.timestamp())


def _post_analytics(user, request_event_action, request_event_label, request_dict={}):
    if plugin.GoogleAnalyticsPlugin.google_analytics_id:
        # retrieve GA client ID from the browser if available
        cookie_header = request.environ.get('HTTP_COOKIE', '')
        match = GA_COOKIE_FORMAT.search(cookie_header)
        if match:
            cid = match.group(1)
        else:
            # Fallback: generate "digits.digits" format
            if user:
                day_timestamp = getStartOfDayInt()
                """Hash username (avoid PII)."""
                cid = f"{int(hashlib.md5(six.ensure_binary(user, encoding='utf-8')).hexdigest(), 16) % 2147483647}.{day_timestamp}"
            else:
                cid = make_daily_client_id()

        # https://developers.google.com/analytics/devguides/collection/ga4/user-id?client_type=gtag
        # https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference?client_type=firebase#payload_geo_info
        if user:
            # Hash username to safe user_id (avoid PII).
            user_id = {"user_id": hashlib.md5(six.ensure_binary(user, encoding='utf-8')).hexdigest()}
            app_user_id = {"app_user_id": hashlib.md5(six.ensure_binary(user, encoding='utf-8')).hexdigest()}
        else:
            user_id = {}
            app_user_id = {}

        page_location = _safe_param(f"{request.url}", 1000)
        referrer = _safe_param(request.environ.get('HTTP_REFERER', ''), 420)

        # CloudFront geo headers
        geo_context = {}
        city = request.headers.get("CloudFront-Viewer-City")
        if city:
            geo_context["city"] = city
        country_region = request.headers.get("CloudFront-Viewer-Country-Region")
        if country_region:
            geo_context["region_id"] = country_region
        country = request.headers.get("CloudFront-Viewer-Country")
        if country:
            geo_context["country_id"] = country
        if request.headers.get("CloudFront-Is-Mobile-Viewer") == "true":
            device_category = "mobile"
        elif request.headers.get("CloudFront-Is-Tablet-Viewer") == "true":
            device_category = "tablet"
        elif request.headers.get("CloudFront-Is-Desktop-Viewer") == "true":
            device_category = "desktop"
        else:
            device_category = "desktop"
        data_dict = {
            "user_agent": request.headers.get('User-Agent'),
            "client_id": cid,
            **user_id,  # Only used when GA4 user_id tracking is enabled (future state)
            "user_location": {
                **geo_context
            },
            "device": {
                "category": device_category
            },
            "events": [
                {
                    "name": "page_view",
                    "params": {
                        "session_id": getStartOfHourInt(),  # Group sessions by the hour for a client_id
                        "page_location": page_location,
                        "page_referrer": referrer,
                        "page_title": _safe_param(request_event_label, 300),
                        "engagement_time_msec": 1,
                        "logged_in": "yes" if user else "no",  # custom dimension
                        **app_user_id  # custom dimension: based off GTM/GA4 'angulartics user id'
                    }
                },
                {
                    "name": "ckan_api_call",
                    "params": {
                        "session_id": getStartOfHourInt(),  # Group sessions by the hour for a client_id
                        "event_category": request.environ['HTTP_HOST'] + " CKAN API Request",  # Legacy UA that is now a custom dimensions
                        **_split_param(request_event_action, "action"),  # custom dimension
                        **_split_param(request_event_label, "label"),  # custom dimension
                        "page_location": page_location,
                        "page_referrer": referrer,
                        "logged_in": "yes" if user else "no",  # custom dimension
                        **app_user_id  # custom dimension: based off GTM/GA4 'angulartics user id'
                    }
                }
            ]
        }
        plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)


def action(get_request_data_function, core_function, api_action, ver):
    try:
        function = get_action(api_action)
        side_effect_free = getattr(function, 'side_effect_free', False)
        request_data = get_request_data_function(try_url_params=side_effect_free)
        capture_api_actions = plugin.GoogleAnalyticsPlugin.capture_api_actions

        # Only send api actions if it is in the capture_api_actions dictionary
        if api_action in capture_api_actions and isinstance(request_data, dict):
            api_action_label = capture_api_actions.get(api_action)

            parameter_value = request_data.get('id', '')
            if parameter_value == '' and 'resource_id' in request_data:
                parameter_value = request_data['resource_id']
            if parameter_value == '' and 'q' in request_data:
                parameter_value = request_data['q']
            if parameter_value == '' and 'query' in request_data:
                parameter_value = request_data['query']
            if parameter_value == '' and 'sql' in request_data:
                parameter_value = _alter_sql(request_data['sql'])

            event_action = "{0} - {1}".format(api_action, request.environ['PATH_INFO'].replace('/api/3/', ''))
            event_label = api_action_label.format(parameter_value)
            _post_analytics(g.user, event_action, event_label, request_data)
    except Exception:
        log.debug(exc_info=True)
        pass
    return core_function(api_action, ver=ver)
