# encoding: utf-8

import hashlib
import logging

from ckantoolkit import g, get_action, request

from . import plugin

log = logging.getLogger('ckanext.googleanalytics')


def _alter_sql(sql_query):
    '''Quick and dirty altering of sql to prevent injection'''
    sql_query = sql_query.lower()
    sql_query = sql_query.replace('select', 'CK_SEL')
    sql_query = sql_query.replace('insert', 'CK_INS')
    sql_query = sql_query.replace('update', 'CK_UPD')
    sql_query = sql_query.replace('upsert', 'CK_UPS')
    sql_query = sql_query.replace('declare', 'CK_DEC')
    sql_query = sql_query[:450].strip()
    return sql_query


def _post_analytics(user, request_event_action, request_event_label, request_dict={}):
    if plugin.GoogleAnalyticsPlugin.google_analytics_id:
        data_dict = {
            "v": 1,
            "tid": plugin.GoogleAnalyticsPlugin.google_analytics_id,
            "cid": hashlib.md5(user).hexdigest(),
            # customer id should be obfuscated
            "t": "event",
            "dh": request.environ['HTTP_HOST'],
            "dp": request.environ['PATH_INFO'],
            "dr": request.environ.get('HTTP_REFERER', ''),
            "ec": request.environ['HTTP_HOST'] + " CKAN API Request",
            "ea": request_event_action,
            "el": request_event_label
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
    except Exception as e:
        log.debug(e)
        pass
    return core_function(api_action, ver=ver)
