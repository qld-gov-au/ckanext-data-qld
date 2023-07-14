import pytest
import mock
from ckan.tests import helpers


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context")
@mock.patch("ckanext.data_qld.actions._send_mail", lambda *args, **kwargs: None)
class TestDataRequestCommentSearch:
    """
    We should be able to find a datarequest by related comment title/content

    The mock prevent _send_mail from creating unnessesary background jobs
    """
    def test_search_by_comment(self, user, datarequest_factory, comment_factory):
        datarequest = datarequest_factory()

        result = helpers.call_action("list_datarequests", q="riverside")
        assert result["count"] == 0
        assert not result["result"]

        comment_factory(
            user_id=user["id"],
            entity_name=datarequest["id"],
            entity_type="datarequest",
            subject="metallica",
            comment="riverside"
        )

        result = helpers.call_action("list_datarequests", q="riverside")
        assert result["count"] == 1
        assert result["result"][0]["id"] == datarequest["id"]

        result = helpers.call_action("list_datarequests", q="metallica")
        assert result["count"] == 1
        assert result["result"][0]["id"] == datarequest["id"]

    def test_proper_sort(self, user, datarequest_factory, comment_factory):
        """We have to ensure, that we are preserving a proper sorting order,
        because we are adding items to results after an original action"""
        dr1 = datarequest_factory(title="riverside 1")
        dr2 = datarequest_factory(title="riverside 2")
        dr3 = datarequest_factory()

        comment_factory(
            user_id=user["id"],
            entity_name=dr3["id"],
            entity_type="datarequest",
            comment="riverside"
        )

        result = helpers.call_action("list_datarequests", q="riverside")
        assert [dr["id"] for dr in result["result"]] == [dr3["id"], dr2["id"], dr1["id"]]

        result = helpers.call_action("list_datarequests", q="riverside", sort="asc")
        assert [dr["id"] for dr in result["result"]] == [dr1["id"], dr2["id"], dr3["id"]]
