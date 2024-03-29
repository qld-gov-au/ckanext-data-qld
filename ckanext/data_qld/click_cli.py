# encoding: utf-8

import click

from ckanext.data_qld import command_functions

# Click commands for CKAN 2.9 and above


@click.group()
def data_qld():
    """ Queensland Government Open Data commands
    """
    pass


@data_qld.command()
def migrate_extras():
    """Migrates legacy field values that were added as free extras to datasets
    to their schema counterparts.
    """
    command_functions.migrate_extras()


@data_qld.command()
def demote_publishers():
    """Demotes any existing 'publisher-*' users from admin to editor
    in their respective organisations.
    """
    command_functions.demote_publishers()


@data_qld.command()
def send_email_dataset_due_to_publishing_notification():
    """
    Send datasets due to publishing to the contact email.
    """
    command_functions.send_email_dataset_due_to_publishing_notification()


@data_qld.command()
def send_email_dataset_overdue_notification():
    """
    Send datasets overdue to the contact email.
    """
    command_functions.send_email_dataset_overdue_notification()


@data_qld.command()
def update_missing_values():
    """
    Update missing values in datasets/resources.
    Dataset metadata fields checked:
        - de_identified_data
        - data_last_updated
    Resource metadata fields checked:
        - nature_of_change
        - last_modified
    Migrate the existing field `resource_visibility` and map to two new fields
        - resource_visible
        - governance_acknowledgement
    """
    command_functions.update_missing_values()


def get_commands():
    return [data_qld]
