import logging

from ckan.lib.base import BaseController, render
from ckan.plugins.toolkit import get_action, request
from ckanext.data_qld.logic import helpers
from ckanext.data_qld.logic import export_helpers

log = logging.getLogger(__name__)

# @TODO: Reset this to 60
DATAREQUEST_OPEN_MAX_DAYS = 60
# @TODO: Reset this to 10
COMMENT_NO_REPLY_MAX_DAYS = 5


class ReportingController(BaseController):

    def index(self, org_id=None, start_date=None, end_date=None):

        # @TODO: handle timezone conversion?
        year, month = helpers.get_year_month(start_date, end_date)
        start_date, end_date = helpers.get_report_date_range(year, month)

        extra_vars = {}

        if org_id:
            org = get_action('organization_show')({}, {'id': org_id})

            extra_vars = {
                'org_id': org_id,
                'org_name': org['title'],
                'org_followers': org['num_followers'],
                'start_date': start_date,
                'end_date': end_date,
                'metrics': helpers.gather_metrics(org_id, start_date, COMMENT_NO_REPLY_MAX_DAYS, DATAREQUEST_OPEN_MAX_DAYS),
                'datarequest_open_max_days': DATAREQUEST_OPEN_MAX_DAYS,
                'comment_no_reply_max_days': COMMENT_NO_REPLY_MAX_DAYS
            }

        return render(
            'reporting/index.html',
            extra_vars=extra_vars
        )

    def export(self):
        import csv
        from pylons import response

        # @TODO: Restrict access to Sysadmin, Admin and Editor roles

        # @TODO: dynamic start date
        start_date = '2020-01-01'

        # @TODO: Get user's orgs
        org_ids = [
            'd4e2967a-aa3a-48bb-bb3b-2202b79f53e4', 'd92d8f2f-b704-47e7-b5a3-67fd97f352f2'
        ]

        report_config = export_helpers.get_report_config()

        row_order, row_properties = export_helpers.get_row_order_and_properties(report_config)

        # csv_header_row = ['""']
        csv_header_row = ['']

        dict_csv_rows = {}

        for key in row_properties:
            dict_csv_rows[key] = []

        closing_circumstances = [c['circumstance'] for c in helpers.get_closing_circumstance_list()]

        for circumstance in closing_circumstances:
            key = 'Closed data requests - %s' % circumstance
            row_order.append(key)
            dict_csv_rows[key] = []

        # Gather all the metrics for each organisation
        for org_id in org_ids:
            export_helpers.add_org_metrics_to_report(
                org_id,
                start_date,
                csv_header_row,
                row_properties,
                dict_csv_rows,
                closing_circumstances,
                COMMENT_NO_REPLY_MAX_DAYS,
                DATAREQUEST_OPEN_MAX_DAYS
            )

        return export_helpers.output_report_csv(csv_header_row, row_order, dict_csv_rows)

        # Compile the CSV output
        output = ''

        output += ','.join(csv_header_row)

        for label in row_order:
            output += '\n"%s",' % label + ','.join(dict_csv_rows[label])

        return '<pre>%s</pre>' % output

        # filename = 'report.csv'
        #
        # with open('/tmp/' + filename, 'wb') as csvfile:
        #     csv_writer = csv.writer(csvfile, delimiter=',',
        #                     ```        quotechar='"', quoting=csv.QUOTE_MINIMAL)
        #     # Add the header row
        #     csv_writer.writerow(csv_header_row)
        #     # Iterate through the results, parse each result and output to csv file
        #     for key, value in data.items():
        #         if key == 'organization_followers':
        #             try:
        #                 csv_writer.writerow(generate_report_row(result))
        #             except Exception, e:
        #                 print(e)
        #
        # fh = open('/tmp/' + filename)
        #
        # response.headers[b'Content-Type'] = b'text/csv; charset=utf-8'
        # response.headers[b'Content-Disposition'] = b"attachment;filename=%s" % filename
        #
        # return fh.read()


    def datasets(self, org_id, metric):

        # @TODO: Validation
        start_date = request.GET.get('start_date', None),
        end_date = request.GET.get('end_date', None)

        if metric == 'no-reply':
            datasets = get_action('datasets_no_replies_after_x_days')(
                    {},
                    {
                        'org_id': org_id,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                )

        return render(
            'reporting/datasets.html',
            extra_vars={
                'org_id': org_id,
                'datasets': datasets,
                'metric': metric,
            }
        )

    def datarequests(self, org_id, metric):
        """Displays a list of data requests for the given organisation based on the desired metric"""

        circumstance = None

        if metric == 'no-comments':
            datarequests = get_action('open_datarequests_no_comments_after_x_days')({}, org_id)
        elif metric == 'open-max-days':
            datarequests = get_action('datarequests_open_after_x_days')({}, {'org_id': org_id, 'days': DATAREQUEST_OPEN_MAX_DAYS})

        else:
            circumstance = request.GET.get('circumstance', None)
            datarequests = get_action('datarequests_for_circumstance')(
                        {},
                        {
                            'org_id': org_id,
                            'circumstance': circumstance
                        }
                    )

        return render(
            'reporting/datarequests.html',
            extra_vars={
                'org_id': org_id,
                'datarequests': datarequests,
                'metric': metric,
                'circumstance': circumstance
            }
        )
