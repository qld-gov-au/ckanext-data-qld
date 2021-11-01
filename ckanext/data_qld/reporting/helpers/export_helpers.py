import csv
import json
import logging
import os
from tempfile import gettempdir

from ckan.common import config
from ckanext.data_qld.reporting.helpers import helpers
from datetime import datetime
from pylons import response

log = logging.getLogger(__name__)


def csv_report_config(report_type):
    """Load a CSV report config file specified in the ini file, or
    fall back to predefined file in the extension"""
    path = config.get('ckan.reporting.json_config', os.path.dirname(os.path.realpath(__file__)) + '/../{0}_report_csv.json'.format(report_type))

    with open(path) as json_data:
        return json.load(json_data)


def csv_row_order_and_properties(report_config):
    """Set the desired row order for the CSV file.
    This is necessary as the metric rows are loaded in
    semi-random order from the dict_csv_rows dictionary
    """
    row_order = []
    row_properties = {}

    for i in range(len(report_config) + 1):
        for key, settings in report_config.items():
            if settings['order'] == i:
                row_order.append(key)
                row_properties[key] = settings
                continue

    return row_order, row_properties


def engagement_csv_add_org_metrics(org, start_date, end_date, csv_header_row, row_properties, dict_csv_rows, closing_circumstances,
                                   comment_no_reply_max_days, datarequest_open_max_days):
    """
    Add engagement reporting metrics for a specific organisation to the CSV data
    :param org:
    :param start_date:
    :param end_date:
    :param csv_header_row:
    :param row_properties:
    :param dict_csv_rows:
    :param closing_circumstances:
    :param comment_no_reply_max_days:
    :param datarequest_open_max_days:
    :return:
    """
    metrics = helpers.gather_engagement_metrics(org.get('id', ''), start_date, end_date, comment_no_reply_max_days,
                                                datarequest_open_max_days)

    csv_header_row.append(org.get('title', ''))

    for key, settings in row_properties.items():
        if settings['type'] not in ['complex', 'length']:
            metric_value = metrics.get(settings['property'], '-')
            dict_csv_rows[key].append(str(int(metric_value)))
        elif settings['type'] == 'length':
            metric_value = len(metrics.get(settings['property'], {}))
            dict_csv_rows[key].append(str(int(metric_value)))
        elif settings['type'] == 'complex':
            metric_value = metrics.get(settings['property'], {})[settings['element']]
            dict_csv_rows[key].append(str(int(metric_value)))

    # Output the closing circumstances rows:
    datarequest_metrics = metrics.get('datarequests', {})

    circumstance_metrics = datarequest_metrics.get('circumstances', {})
    no_circumstance_closures = datarequest_metrics.get('no_circumstance', {})

    for circumstance in closing_circumstances:
        metric_dict = circumstance_metrics.get(circumstance, {})
        dict_csv_rows['Closed data requests - %s' % circumstance].append(str(int(metric_dict.get('count', 0))))

    for n in no_circumstance_closures:
        dict_csv_rows['Closed data requests - Closed %s' % n.replace('_', ' ')].append(
            str(int(no_circumstance_closures[n]['count'])))

    # Now the average closing time for each circumstance
    for circumstance in closing_circumstances:
        metric_dict = circumstance_metrics.get(circumstance, {})
        dict_csv_rows['Average days closed data request - %s' % circumstance].append(str(int(metric_dict.get('average', 0))))

    # Now the average closing time for no circumstance data request closures
    for n in no_circumstance_closures:
        dict_csv_rows['Average days closed data request - Closed %s' % n.replace('_', ' ')].append(
            str(int(no_circumstance_closures[n].get('average', 0))))

    dict_csv_rows['Average days closed data requests - overall'].append(str(int(datarequest_metrics.get('average_overall', 0))))


def admin_csv_add_org_metrics(org, csv_header_row, row_properties, dict_csv_rows, permission):
    """
    Add admin eporting metrics for a specific organisation to the CSV data
    :param org:
    :param csv_header_row:
    :param row_properties:
    :param dict_csv_rows:
    :return:
    """
    metrics = helpers.gather_admin_metrics(org.get('id', ''), permission)

    csv_header_row.append(org.get('title', ''))

    for key, settings in row_properties.items():
        if settings['type'] not in ['complex', 'length']:
            metric_value = metrics.get(settings['property'], '-')
            dict_csv_rows[key].append(str(int(metric_value)))
        elif settings['type'] == 'length':
            metric_value = len(metrics.get(settings['property'], {}))
            dict_csv_rows[key].append(str(int(metric_value)))
        elif settings['type'] == 'complex':
            metric_value = metrics.get(settings['property'], {})[settings['element']]
            dict_csv_rows[key].append(str(int(metric_value)))


def output_report_csv(csv_header_row, row_order, dict_csv_rows, report_type):
    filename = '{0}-{1}-report.csv'.format(datetime.now().strftime("%Y-%m-%d-%H-%M"), report_type)
    filepath = gettempdir() + '/' + filename

    try:
        with open(filepath, 'wb') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(csv_header_row)
            for label in row_order:
                row = [label] + dict_csv_rows[label]
                csv_writer.writerow(row)

        fh = open(filepath)

        response.headers[b'Content-Type'] = b'text/csv; charset=utf-8'
        response.headers[b'Content-Disposition'] = b"attachment;filename=%s" % filename

        return fh.read()
    except Exception as e:
        log.error('Error creating {0} report CSV export file: {1}'.format(report_type, filepath))
        log.error(str(e))
