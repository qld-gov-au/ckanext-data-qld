from ckan.common import config

DATAREQUEST_OPEN_MAX_DAYS = config.get('ckan.reporting.datarequest_open_max_days', 60)
COMMENT_NO_REPLY_MAX_DAYS = config.get('ckan.reporting.comment_no_reply_max_days', 10)
