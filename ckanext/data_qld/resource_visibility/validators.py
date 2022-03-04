# encoding: utf-8

from ckantoolkit import _, missing, StopOnError

from ckanext.data_qld.resource_visibility import helpers as resource_visibility_helpers
from ckanext.data_qld import helpers as data_qld_helpers


def resource_visibility(key, data, errors, context):
    """
    Users must select one of the correct option
    based on the package.de_identified_data.
    """
    if data_qld_helpers.is_delete_request():
        return

    de_identified_data = data.get((u'de_identified_data',))

    res, index, field = key
    res_id = data.get((u'resources', index, u'id'), None)
    resource_data_updated = context.get('resource_data_updated', {})

    # None is a new resource.
    processed_res_id = resource_data_updated.get('id') if resource_data_updated else None
    value = str(data.get(key, '')) if data[key] is not missing else ''
    api_request = data_qld_helpers.is_api_request()
    # Validate all resources if its coming from the package_show API otherwise just validate the resource that is being updated
    if api_request or res_id == processed_res_id:
        options = resource_visibility_helpers.get_select_field_options('resource_visibility')
        option_values = [option.get('value') for option in options]
        if de_identified_data == 'YES':
            # Field is required.
            if len(value) == 0:
                errors[key].append(
                    _('This dataset has been recorded as containing de-identified data. '
                      'A re-identification risk governance acknowledgement for this resource must be made prior to publishing')
                )
                raise StopOnError
            # First option will be disabled.
            if value == options[0].get('value'):
                errors[key].append(_('Illegal option selected'))
                raise StopOnError
        else:
            # Second option will be disabled.
            if value == options[1].get('value'):
                errors[key].append(_('Illegal option selected'))
                raise StopOnError
            # Blank empty strings are allowed for non de_identified_data
            option_values.append('')

        # Check if value is part of the options
        if value not in option_values:
            errors[key].append(_('Value must be one of {}'.format(option_values)))
            raise StopOnError
