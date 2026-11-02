import pytest
import mock
import random
import string

from ckan.tests import helpers


@pytest.mark.usefixtures("with_plugins", "with_request_context")
@mock.patch("ckanext.datarequests.actions._send_mail", lambda *args, **kwargs: None)
class TestDataRequestCommentSearch:
    """
    We should be able to find a datarequest by related comment title/content

    The mock prevent _send_mail from creating unnecessary background jobs
    """
    def test_search_by_comment(self, user, datarequest_factory, comment_factory):
        datarequest = datarequest_factory()
        key = ''.join(random.choices(string.ascii_letters, k=10))

        result = helpers.call_action("list_datarequests", q=key)
        assert result["count"] == 0
        assert not result["result"]

        comment_factory(
            user_id=user["id"],
            entity_name=datarequest["id"],
            entity_type="datarequest",
            subject="metallica",
            comment=key
        )

        result = helpers.call_action("list_datarequests", q=key)
        assert result["count"] == 1
        assert result["result"][0]["id"] == datarequest["id"]

        result = helpers.call_action("list_datarequests", q="metallica")
        assert result["count"] == 1
        assert result["result"][0]["id"] == datarequest["id"]

    def test_proper_sort(self, user, datarequest_factory, comment_factory):
        """We have to ensure, that we are preserving a proper sorting order,
        because we are adding items to results after an original action"""
        prefix = ''.join(random.choices(string.ascii_letters, k=10))
        dr1 = datarequest_factory(title=f"{prefix} 1")
        dr2 = datarequest_factory(title=f"{prefix} 2")
        dr3 = datarequest_factory()

        comment_factory(
            user_id=user["id"],
            entity_name=dr3["id"],
            entity_type="datarequest",
            comment=prefix
        )

        result = helpers.call_action("list_datarequests", q=prefix)
        assert [dr["id"] for dr in result["result"]] == [dr3["id"], dr2["id"], dr1["id"]]

        result = helpers.call_action("list_datarequests", q=prefix, sort="asc")
        assert [dr["id"] for dr in result["result"]] == [dr1["id"], dr2["id"], dr3["id"]]
