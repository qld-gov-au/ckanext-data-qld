# encoding: utf-8

import ckan.plugins as p

import blueprints
from .reporting import blueprints as reporting_blueprints
import click_cli


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IClick)

    # IBlueprint

    def get_blueprint(self):
        return [blueprints.blueprint, reporting_blueprints.blueprint]

    # IClick

    def get_commands(self):
        return click_cli.get_commands()
