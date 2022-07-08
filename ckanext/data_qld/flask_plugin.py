# encoding: utf-8

import ckan.plugins as p

from . import blueprints, click_cli
from .reporting import blueprints as reporting_blueprints


class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IBlueprint)
    p.implements(p.IClick)

    # IBlueprint

    def get_blueprint(self):
        return [blueprints.blueprint, reporting_blueprints.blueprint]

    # IClick

    def get_commands(self):
        return click_cli.get_commands()
