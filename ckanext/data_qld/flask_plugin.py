# encoding: utf-8

import ckan.plugins as p

import click_cli
import datarequest_view
import dataset_view


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IClick)

    # IBlueprint

    def get_blueprint(self):
        return datarequest_view.get_blueprints().extend(dataset_view.get_blueprints())

    # IClick

    def get_commands(self):
        return click_cli.get_commands()
