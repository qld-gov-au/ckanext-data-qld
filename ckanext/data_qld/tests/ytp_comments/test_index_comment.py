import pytest
import factory

import ckan.model as model
import ckan.lib.search as search
from ckan.tests import helpers

from ckanext.ytp.comments import model as ytp_model


class Comment(factory.Factory):
    """A factory class for creating ytp comment. It must accept user_id and
    package_name, because I don't want to create extra entities in database
    during tests"""

    class Meta:
        model = ytp_model.Comment

    user_id = None
    package_name = None
    subject = "comment-subject"
    comment = "comment-text"

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        kwargs["url"] = "/dataset/{}".format(kwargs["package_name"])

        return helpers.call_action(
            "comment_create", context={"user": kwargs["user_id"], "ignore_auth": True}, **kwargs
        )


@pytest.mark.usefixtures("with_plugins", "clean_index", "clean_db", "with_request_context")
class TestIndexComment:
    """We are indexing comments for a dataset (title and content) into SOLR to make
    it available with default package_search"""
    def test_search_by_comment(self, user, dataset):
        Comment(user_id=user["id"], package_name=dataset["name"])

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
    def test_search_different_chunks(self, user, dataset, message):
        Comment(user_id=user["id"], package_name=dataset["name"], comment=message)

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
