# encoding: utf-8

import json
import logging

from ckantoolkit import request, get_action, ValidationError, get_endpoint, h

log = logging.getLogger(__name__)


def add_deletion_of_dataset_reason(data_dict):
    deletion_reason = ''
    if get_endpoint()[1] == 'action':
        body = json.loads(request.body)
        deletion_reason = body.get('deletion_reason', '')
    else:
        params = request.params.items()
        for param in params:
            if 'deletion_reason' in param:
                deletion_reason = param[1]

    if not deletion_reason:
        if get_endpoint()[1] == 'action':
            raise ValidationError('Missing deletion_reason field.')
        else:
            h.flash_error('Missing deletion reason.')
            return h.redirect_to('/dataset/edit/' + data_dict.id)

    if len(deletion_reason) < 10:
        if get_endpoint()[1] == 'action':
            raise ValidationError('Field deletion_reason must not less than 10 characters.')
        else:
            h.flash_error('Deletion reason must not less than 10 characters.')
            return h.redirect_to('/dataset/edit/' + data_dict.id)

    if len(deletion_reason) > 250:
        if get_endpoint()[1] == 'action':
            raise ValidationError('Field deletion_reason must not more than 250 characters.')
        else:
            h.flash_error('Deletion reason must not more than 250 characters.')
            return h.redirect_to('/dataset/edit/' + data_dict.id)

    get_action('package_patch')({}, {'id': data_dict.id, 'deletion_reason': deletion_reason})
