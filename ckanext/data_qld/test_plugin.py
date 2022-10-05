# encoding: utf-8

import ckantoolkit as tk

from ckan import plugins

from ckanext.data_qld.tests.conftest import DatasetFactory, ResourceFactory
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
            qld_test_create_dataset,
            qld_test_purge_dataset,
            qld_test_patch_dataset,
            qld_test_create_resource_for_dataset,
            qld_test_trigger_notify_privacy_assessment_result,
        )

        return {"{}".format(func.__name__): func for func in actions}


@tk.side_effect_free
def qld_test_create_dataset(context, data_dict):
    package = DatasetFactory(**data_dict)
    ResourceFactory(package_id=package["id"], bdd=True)

    return package


@tk.side_effect_free
def qld_test_purge_dataset(context, data_dict):
    context = _make_context()
    pkg_dict = tk.get_action("package_show")(context, data_dict)

    tk.get_action("dataset_purge")(context, data_dict)
    tk.get_action("organization_purge")(context, {"id": pkg_dict["owner_org"]})


@tk.side_effect_free
def qld_test_patch_dataset(context, data_dict):
    tk.get_action("package_patch")(_make_context(), data_dict)


@tk.side_effect_free
def qld_test_create_resource_for_dataset(context, data_dict):
    data_dict['bdd'] = True
    resource = ResourceFactory(**data_dict)

    return resource


@tk.side_effect_free
def qld_test_trigger_notify_privacy_assessment_result(context, data_dict):
    data = utils.get_updated_privacy_assessment_result()

    if not data:
        return

    for maintainer_email, updated_data in data.items():
        utils.send_notifications(maintainer_email, updated_data.values())
        utils._clear_upd_assessment_result_data()


def _make_context():
    context = {"ignore_auth": True}
    user_obj = tk.get_action("get_site_user")(context, {})
    return {"user": user_obj['name']}
