import json
import logging
import os

from ckan.plugins.toolkit import get_action
from ckanext.data_qld.logic import helpers

log = logging.getLogger(__name__)


def get_report_config():
    path = os.path.dirname(os.path.realpath(__file__)) + '/../report_csv.json'

    log.debug(path)

    #     Load some config info from a json file
    #     '''
    #     path = config.get('ckan.workflow.json_config',
    #                       '/usr/lib/ckan/default/src/ckanext-workflow/ckanext/workflow/example.settings.json')
    with open(path) as json_data:
        return json.load(json_data)


def get_row_order_and_properties(report_config):
    row_order = []
    row_properties = {}

    for i in range(len(report_config) + 1):
        for key, settings in report_config.items():
            if settings['order'] == i:
                row_order.append(key)
                row_properties[key] = settings
                continue

    return row_order, row_properties


def add_org_metrics_to_report(org_id, start_date, csv_header_row, row_properties, dict_csv_rows, closing_circumstances, comment_no_reply_max_days, datarequest_open_max_days):
    # @TODO: de-dupe
    org = get_action('organization_show')({}, {'id': org_id})

    # @TODO: dynamic start date
    metrics = helpers.gather_metrics(org_id, start_date, comment_no_reply_max_days, datarequest_open_max_days)

    # csv_header_row.append('"%s"' % org['title'])
    csv_header_row.append(org['title'])

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
    import csv
    from pylons import response

    filename = 'report.csv'

    with open('/tmp/' + filename, 'wb') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Add the header row
        csv_writer.writerow(csv_header_row)
        # Iterate through the results, parse each result and output to csv file
        for label in row_order:
            # csv_writer.writerow('"%s",' % label + ','.join(dict_csv_rows[label]))
            row = [label] + dict_csv_rows[label]
            csv_writer.writerow(row)

    fh = open('/tmp/' + filename)

    response.headers[b'Content-Type'] = b'text/csv; charset=utf-8'
    response.headers[b'Content-Disposition'] = b"attachment;filename=%s" % filename

    return fh.read()
