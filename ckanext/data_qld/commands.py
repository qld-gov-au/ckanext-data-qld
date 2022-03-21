# encoding: utf-8

from ckanext.data_qld.command_functions import demote_publishers, migrate_extras

from ckan.lib.cli import CkanCommand


class MigrateExtras(CkanCommand):
    """Migrates legacy field values that were added as free extras to datasets to their schema counterparts.
    """

    summary = __doc__.split('\n')[0]

    def __init__(self, name):

        super(MigrateExtras, self).__init__(name)

    def command(self):
        self._load_config()

        return migrate_extras()


class DemotePublishers(CkanCommand):
    """Demotes any existing 'publisher-*' users from admin to editor in their respective organisations
    """

    summary = __doc__.split('\n')[0]

    def __init__(self, name):
        super(DemotePublishers, self).__init__(name)
        self.parser.add_option('-u', '--username_prefix', dest='username_prefix', help='Only demote usernames starting with this prefix', type=str, default='publisher-')

    def command(self):
        self._load_config()

        username_prefix = self.options.username_prefix

        return demote_publishers(username_prefix)
