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
    command_functions.migrate_extras()


@data_qld.command()
def demote_publishers():
    command_functions.demote_publishers()


def get_commands():
    return [data_qld]
