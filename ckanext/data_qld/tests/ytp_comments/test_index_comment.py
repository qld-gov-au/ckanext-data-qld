import pytest

import ckan.model as model
import ckan.lib.search as search
from ckan.tests import helpers

from ckanext.ytp.comments import model as ytp_model


@pytest.mark.usefixtures("with_plugins", "clean_index", "clean_db", "with_request_context")
class TestIndexComment:
    """We are indexing comments for a dataset (title and content) into SOLR to make
    it available with default package_search"""
    def test_search_by_comment(self, user, dataset, comment_factory):
        comment_factory(user_id=user["id"], entity_name=dataset["name"])

        result = search.query_for(model.Package).run({"q": "comment-subject"})
        assert result["count"] == 1

        result = search.query_for(model.Package).run({"q": "comment-text"})
        assert result["count"] == 1

        result = search.query_for(model.Package).run({"q": "something-else"})
        assert result["count"] == 0

    @pytest.mark.parametrize(
        u"message",
        [
            "test-me",
            "sm",
            "RIVERSIDE"
        ],
    )
    def test_search_different_chunks(self, user, dataset, comment_factory, message):
        comment_factory(user_id=user["id"], entity_name=dataset["name"], comment=message)

        result = search.query_for(model.Package).run({"q": message})
        assert result["count"] == 1

    def test_package_create_do_not_create_threads(self, dataset):
        """Test if we aren't going to create an empty comment thread while
        creating/updating a package. I had to use custom function, instead of
        a core ytp-comment action `thread_show`, because it has a side effects
        besides showing a thread.

        The `dataset` fixture is actually creating a dataset.
        """
        assert model.Session.query(ytp_model.CommentThread).all()

        helpers.call_action("package_patch", id=dataset["id"], notes="xxx")

        assert model.Session.query(ytp_model.CommentThread).all()
