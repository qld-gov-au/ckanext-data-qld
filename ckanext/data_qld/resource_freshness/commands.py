# encoding: utf-8

from ckan.lib.cli import CkanCommand

import command_functions


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
        command_functions.send_email_dataset_due_to_publishing_notification()


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
        command_functions.send_email_dataset_overdue_notification()
