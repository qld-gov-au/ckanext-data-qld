import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as toolkit

missing = df.missing
h = toolkit.h


def resource_visibility(key, data, errors, context):
    """
    Users must select one of the correct option
    based on the package.de_identified_data.
    """
    options = h.data_qld_get_select_field_options('resource_visibility')
    de_identified_data = data.get((u'de_identified_data',))

    res, index, field = key
    res_id = data.get((u'resources', index, u'id'), None)
    resource_data_updated = context.get('resource_data_updated', {})

    # None is a new resource.
    processed_res_id = None
    if resource_data_updated:
        processed_res_id = resource_data_updated.get('id')

    if data[key] is not missing:
        value = str(data.get(key, ''))

        if res_id == processed_res_id:
            if de_identified_data == 'YES':
                # Field is required.
                if len(value) == 0:
                    errors[key].append(toolkit._('This dataset has been recorded as containing de-identified data. A re-identification risk governance acknowledgement for this resource must be made prior to publishing'))

                # First option will be disabled.
                if value == options[0].get('value'):
                    errors[key].append(toolkit._('Illegal option selected'))
            else:
                # Second option will be disabled.
                if value == options[1].get('value'):
                    errors[key].append(toolkit._('Illegal option selected'))
    else:
        data.pop(key, None)
