import logging
from ckan.lib.cli import CkanCommand


class SendEmailDatasetDueToPublishingNotification(CkanCommand):
    """
    Send datasets due to publishing to the contact email.
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        self._load_config()
        # Need to do CKAN imports and logger after load config
        from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers
        log = logging.getLogger(__name__)
        log.info('Started command SendEmailDatasetDueToPublishingNotification')
        resource_freshness_helpers.process_email_notification_for_dataset_due_to_publishing()
        log.info('Finished command SendEmailDatasetDueToPublishingNotification')


class SendEmailDatasetOverdueNotification(CkanCommand):
    """
    Send datasets overdue to the contact email.
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        self._load_config()
        # Need to do CKAN imports and logger after load config
        from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers
        log = logging.getLogger(__name__)
        log.info('Started command SendEmailDatasetOverdueNotification')
        resource_freshness_helpers.process_email_notification_for_dataset_overdue()
        log.info('Finished command SendEmailDatasetOverdueNotification')
