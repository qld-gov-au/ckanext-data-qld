import pytest

from ckan.tests.helpers import call_action
from ckan.lib.helpers import url_for

import ckanext.resource_visibility.constants as const
from ckanext.resource_visibility.utils import (
    get_updated_privacy_assessment_result, _clear_upd_assessment_result_data)


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestPrivacyAssessmentResultTracking:
    maintainer = "test@gmail.com"
    assess_result = "0.9 High"

    def test_creation_not_tracked(self, dataset_factory, resource_factory):
        dataset = dataset_factory(author_email=self.maintainer)
        resource_factory(package_id=dataset["id"])
        data = get_updated_privacy_assessment_result()
        assert not data

    def test_updating_tracked(self, dataset_factory, resource_factory):
        dataset = dataset_factory(author_email=self.maintainer)
        resource = resource_factory(package_id=dataset["id"])

        data = get_updated_privacy_assessment_result()
        assert not data

        call_action("resource_patch", {"ignore_auth": True},
                    id=resource["id"],
                    privacy_assessment_result=self.assess_result)

        data = get_updated_privacy_assessment_result()
        assert data[self.maintainer]

        tracked_data = data[self.maintainer][resource["id"]]
        assert tracked_data

        assert tracked_data["id"] == resource["id"]
        assert tracked_data["maintainer"] == self.maintainer
        assert tracked_data["package_id"] == resource["package_id"]
        assert tracked_data[const.FIELD_ASSESS_RESULT] == self.assess_result

        resource_external_url = url_for("resource.read",
                                        id=resource["package_id"],
                                        resource_id=resource["id"],
                                        _external=True)
        assert tracked_data["url"] == resource_external_url

    def test_clean_updated_stack(self, dataset_factory, resource_factory):
        dataset = dataset_factory(author_email=self.maintainer)
        resource = resource_factory(package_id=dataset["id"])

        call_action("resource_patch", {"ignore_auth": True},
                    id=resource["id"],
                    privacy_assessment_result=self.assess_result)

        data = get_updated_privacy_assessment_result()
        assert data[self.maintainer]

        _clear_upd_assessment_result_data()

        data = get_updated_privacy_assessment_result()
        assert not data
