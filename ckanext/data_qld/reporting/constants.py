from ckan.common import config

DATAREQUEST_OPEN_MAX_DAYS = int(config.get('ckan.reporting.datarequest_open_max_days', 60))
COMMENT_NO_REPLY_MAX_DAYS = int(config.get('ckan.reporting.comment_no_reply_max_days', 10))
REPORT_TYPE_ENGAGEMENT = "engagement"
REPORT_TYPE_ADMIN = "admin"
REPORT_TYPES = [
    REPORT_TYPE_ENGAGEMENT,
    REPORT_TYPE_ADMIN
]
REPORT_DEIDENTIFIED_NO_SCHEMA_COUNT_FROM = config.get('ckanext.data_qld.reporting.de_identified_no_schema.count_from', '2022-01-01')
