import csv
import json
import logging
import os

from ckan.common import config
from ckanext.data_qld.reporting.helpers import helpers
from pylons import response

log = logging.getLogger(__name__)


def csv_report_config():
    """Load a CSV report config file specified in the ini file, or
    fall back to predefined file in the extension"""
    path = config.get('ckan.reporting.json_config', os.path.dirname(os.path.realpath(__file__)) + '/../report_csv.json')

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


def csv_add_org_metrics(org, start_date, end_date, csv_header_row, row_properties, dict_csv_rows, closing_circumstances,
                        comment_no_reply_max_days, datarequest_open_max_days):
    """
    Add reporting metrics for a specific organisation to the CSV data
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
    metrics = helpers.gather_metrics(org.get('id', ''), start_date, end_date, comment_no_reply_max_days,
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

    # output the closing circumstances rows:
    datarequest_metrics = metrics.get('datarequests', {})

    circumstance_metrics = datarequest_metrics.get('circumstances', {})

    for circumstance in closing_circumstances:
        metric_dict = circumstance_metrics.get(circumstance, {})
        dict_csv_rows['Closed data requests - %s' % circumstance].append(str(int(metric_dict.get('count', 0))))


def output_report_csv(csv_header_row, row_order, dict_csv_rows):
    filename = 'report.csv'

    with open('/tmp/' + filename, 'wb') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(csv_header_row)
        for label in row_order:
            row = [label] + dict_csv_rows[label]
            csv_writer.writerow(row)

    fh = open('/tmp/' + filename)

    response.headers[b'Content-Type'] = b'text/csv; charset=utf-8'
    response.headers[b'Content-Disposition'] = b"attachment;filename=%s" % filename

    return fh.read()
