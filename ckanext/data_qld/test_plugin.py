# encoding: utf-8

import ckantoolkit as tk

from ckan import plugins

import ckanext.resource_visibility.utils as utils


class DataQldTestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IActions)

    def update_config(self, config):
        assert tk.asbool(tk.config.get("ckanext.data_qld.allow_bdd_test_plugin")),\
            'BDD test plugin is not allowed'

    # IActions

    def get_actions(self):
        actions = (
            qld_test_trigger_notify_privacy_assessment_result,
        )

        return {"{}".format(func.__name__): func for func in actions}


@tk.side_effect_free
def qld_test_trigger_notify_privacy_assessment_result(context, data_dict):
    data = utils.get_updated_privacy_assessment_result()

    if not data:
        return

    for maintainer_email, updated_data in data.items():
        utils.send_notifications(maintainer_email, updated_data.values())
        utils._clear_upd_assessment_result_data()
