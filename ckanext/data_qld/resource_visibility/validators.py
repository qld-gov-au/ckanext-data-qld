import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as toolkit
import logging

missing = df.missing
h = toolkit.h
log = logging.getLogger(__name__)


def resource_visibility(key, data, errors, context):
    """
    Users must select one of the correct option
    based on the package.de_identified_data.
    """
    options = h.data_qld_get_select_field_options('resource_visibility')
    de_identified_data = data.get((u'de_identified_data',))
    value = data.get(key, '')

    if value is not missing:
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
