# encoding: utf-8

import logging

from ckantoolkit import request, get_action, ValidationError, h
from ckanext.data_qld import helpers as data_qld_helpers

log = logging.getLogger(__name__)


def add_deletion_of_dataset_reason(context, data_dict):
    # if it's a list - it's a resource deletion
    if isinstance(data_dict, list):
        return

    dataset_id = data_dict.get('id')
    is_api_request = data_qld_helpers.is_api_request()

    if is_api_request:
        # API Controller/View will send all of body data in the data_dict
        # Retrieve value from data_dict
        deletion_reason = data_dict.get('deletion_reason')
    else:
        # UI Controller/View will only send the id in the data_dict
        # Retrieve value from request params
        deletion_reason = request.params.get('deletion_reason')

    if not deletion_reason:
        if is_api_request:
            raise ValidationError('Missing deletion_reason field.')
        else:
            h.flash_error('Missing deletion reason.')
            return h.redirect_to('/dataset/edit/' + dataset_id)

    if len(deletion_reason) < 10:
        if is_api_request:
            raise ValidationError(
                'Field deletion_reason must not less than 10 characters.')
        else:
            h.flash_error('Deletion reason must not less than 10 characters.')
            return h.redirect_to('/dataset/edit/' + dataset_id)

    if len(deletion_reason) > 250:
        if is_api_request:
            raise ValidationError(
                'Field deletion_reason must not more than 250 characters.')
        else:
            h.flash_error('Deletion reason must not more than 250 characters.')
            return h.redirect_to('/dataset/edit/' + dataset_id)

    get_action('package_patch')(
        context, {'id': dataset_id, 'deletion_reason': deletion_reason})
