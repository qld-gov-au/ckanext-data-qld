import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.logic import side_effect_free

import logging
import sqlalchemy
from ckan.model.follower import UserFollowingDataset, UserFollowingGroup
from ckan.model.package import Package
from ckan.model.group import Group
from ckanext.ytp.comments.model import Comment, CommentThread
from ckanext.ytp.comments.notification_models import CommentNotificationRecipient
from sqlalchemy import func, distinct, text
from sqlalchemy.orm import aliased
from ckanext.data_qld.logic import helpers
from ckanext.datarequests import db
from datetime import datetime, timedelta

_and_ = sqlalchemy.and_
_replace_ = func.replace
_session_ = model.Session
check_org_access = helpers.check_org_access
log = logging.getLogger(__name__)

#
ACTIVE_STATE = 'active'
DATAREQUEST_PREFIX = '/datarequest/'
DATAREQUEST_LIKE = DATAREQUEST_PREFIX + '%'
DATASET_PREFIX = '/dataset/'
DATASET_LIKE = DATASET_PREFIX + '%'


def organisation_followers(context, data_dict):
    """
    Return the number of followers for an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(UserFollowingGroup.follower_id)
            )
            .filter(
                _and_(
                    Group.id == org_id,
                    UserFollowingGroup.datetime >= start_date,
                    UserFollowingGroup.datetime <= end_date,
                )
            )
            .join(Group, Group.id == UserFollowingGroup.object_id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_followers(context, data_dict):
    """
    Return the number of followers across all datasets belonging to an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(UserFollowingDataset.follower_id)
            )
            .filter(
                _and_(
                    Package.owner_org == org_id,
                    UserFollowingDataset.datetime >= start_date,
                    UserFollowingDataset.datetime <= end_date,
                )
            )
            .join(Package, Package.id == UserFollowingDataset.object_id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_comments(context, data_dict):
    """
    Total count of active dataset comments across an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(distinct(Comment.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= end_date,
                    Package.owner_org == org_id,
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datarequests(context, data_dict):
    """
    Return the data requests assigned to an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                db.DataRequest
            )
            .filter(
                db.DataRequest.organization_id == org_id,
                func.date(db.DataRequest.open_time) >= start_date,
                func.date(db.DataRequest.open_time) <= end_date,
            )
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequest_comments(context, data_dict):
    """
    Total count of active data request comments across an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                func.count(distinct(Comment.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= end_date,
                    db.DataRequest.organization_id == org_id
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(db.DataRequest, db.DataRequest.id == _replace_(CommentThread.url, DATAREQUEST_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_comment_followers(context, data_dict):
    """
    Number of dataset comment followers at an organization level
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                func.count(distinct(CommentNotificationRecipient.user_id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= end_date,
                    Package.owner_org == org_id
                )
            )
            .join(CommentThread, CommentThread.id == CommentNotificationRecipient.thread_id)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datasets_min_one_comment_follower(context, data_dict):
    """
    Number of Datasets with at least one comment follower
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(distinct(Package.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= end_date,
                    Package.owner_org == org_id
                )
            )
            .join(CommentThread, CommentThread.url == func.concat(DATASET_PREFIX, Package.name))
            .join(CommentNotificationRecipient, CommentNotificationRecipient.thread_id == CommentThread.id)
            # Don't need JOIN ON clause - `comment` table has `comment_thread`.`id` FK
            .join(Comment)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datarequests_min_one_comment_follower(context, data_dict):
    """
    Number of Data Requests across an organisation with at least one comment follower
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                func.count(distinct(db.DataRequest.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= end_date,
                    db.DataRequest.organization_id == org_id
                )
            )
            .join(CommentThread, CommentThread.url == func.concat(DATAREQUEST_PREFIX, db.DataRequest.id))
            .join(CommentNotificationRecipient, CommentNotificationRecipient.thread_id == CommentThread.id)
            .join(Comment, Comment.thread_id == CommentThread.id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datasets_no_replies_after_x_days(context, data_dict):
    """
    Dataset comments that have no replies whatsoever, and it has been > 10 days since the comment was created
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    comment_expected_reply_by_date = data_dict.get('comment_expected_reply_by_date', None)

    check_org_access(org_id)

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        datasets = (
            _session_.query(
                Comment.id,
                Comment.parent_id,
                Comment.creation_date,
                Comment.subject,
                CommentThread.url,
                Package.name,
                comment_reply.parent_id,
                comment_reply.creation_date,
                comment_reply.comment,
                Package.title
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.parent_id == None,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= comment_expected_reply_by_date,
                    Comment.state == ACTIVE_STATE,
                    Package.owner_org == org_id,
                    comment_reply.id == None
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id)
            )
        )

        log.debug(str(datasets))

        return datasets.all()

    except Exception as e:
        log.error(str(e))


def datarequests_no_replies_after_x_days(context, data_dict):
    """
    Data request comments that have no replies whatsoever, and it has been > 10 days since the comment was created
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    comment_expected_reply_by_date = data_dict.get('comment_expected_reply_by_date', None)

    check_org_access(org_id)

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        db.init_db(model)
        return (
            _session_.query(
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date,
                Comment.subject,
                CommentThread.url,
                db.DataRequest.id.label("datarequest_id"),
                db.DataRequest.title,
                comment_reply.parent_id,
                comment_reply.creation_date,
                comment_reply.comment
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.parent_id == None,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= comment_expected_reply_by_date,
                    Comment.state == ACTIVE_STATE,
                    db.DataRequest.organization_id == org_id,
                    comment_reply.id == None
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(db.DataRequest, db.DataRequest.id == _replace_(CommentThread.url, DATAREQUEST_PREFIX, ''))
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id)
            )
        ).all()

    except Exception as e:
        log.error(str(e))


def open_datarequests_no_comments_after_x_days(context, data_dict):
    """
    Data requests that have no comments whatsoever, and it has
    been > 10 days since the data request was opened.
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('start_date', None)
    max_days = int(data_dict.get('comment_no_reply_max_days', 10))

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                db.DataRequest.id,
                db.DataRequest.title,
                db.DataRequest.open_time,
                CommentThread.url,
            )
            .filter(
                _and_(
                    db.DataRequest.organization_id == org_id,
                    db.DataRequest.closed == False,
                    db.DataRequest.open_time >= start_date,
                    db.DataRequest.open_time <= end_date,
                    db.DataRequest.open_time < func.date(db.DataRequest.open_time + text("interval '%i day'" % max_days))
                )
            )
            .outerjoin(CommentThread, CommentThread.url == func.concat(DATAREQUEST_PREFIX, db.DataRequest.id))
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequests_open_after_x_days(context, data_dict):
    """
    Data requests that have no comments whatsoever, and it has
    been > 10 days since the data request was opened.
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)
    max_days = int(data_dict.get('datarequest_open_max_days', 10))

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                db.DataRequest.id,
                db.DataRequest.title,
                db.DataRequest.open_time,
            )
            .filter(
                _and_(
                    db.DataRequest.organization_id == org_id,
                    db.DataRequest.closed == False,
                    db.DataRequest.open_time >= start_date,
                    db.DataRequest.open_time <= end_date,
                    db.DataRequest.open_time < func.date(db.DataRequest.open_time + text("interval '%i day'" % max_days))
                )
            )
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequests_for_circumstance(context, data_dict):
    org_id = data_dict.get('org_id', None)
    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('start_date', None)
    circumstance = data_dict.get('circumstance', None)

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                db.DataRequest
            )
            .filter(
                db.DataRequest.organization_id == org_id,
                db.DataRequest.close_circumstance == circumstance,
                db.DataRequest.open_time >= start_date,
                db.DataRequest.open_time <= end_date,
            )
        ).all()

    except Exception as e:
        log.error(str(e))


def comments_no_replies_after_x_days(context, data_dict):
    """
    Comments that have no replies whatsoever, and it has been > 10 days since the comment was created
    :param context:
    :param data_dict:
    :return:
    """
    thread_url = data_dict.get('thread_url', None)
    start_date = data_dict.get('start_date', None)
    comment_expected_reply_by_date = data_dict.get('comment_expected_reply_by_date', None)

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        return (
            _session_.query(
                CommentThread.url,
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date,
            )
            .filter(
                _and_(
                    CommentThread.url == thread_url,
                    Comment.parent_id == None,
                    Comment.creation_date >= start_date,
                    Comment.creation_date <= comment_expected_reply_by_date,
                    Comment.state == ACTIVE_STATE,
                    comment_reply.id == None
                )
            )
            .join(Comment)
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id)
            )
        ).all()

    except Exception as e:
        log.error(str(e))
