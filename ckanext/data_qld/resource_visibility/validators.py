import ckan.plugins.toolkit as toolkit
import logging

h = toolkit.h
log = logging.getLogger(__name__)


def resource_visibility(key, data, errors, context):
    """
    Sysadmin can select blank value,
    other users must select one of the correct option
    based on the package.de_identified_data.
    """
    options = h.data_qld_get_select_field_options('resource_visibility')
    de_identified_data = data.get((u'de_identified_data',))
    value = data.get(key, '')

    if de_identified_data == 'YES':
        # Field is required.
        if len(value) == 0:
            errors[key].append(toolkit.Invalid('This dataset has been recorded as containing de-identified data. A re-identification risk governance acknowledgement for this resource must be made prior to publishing')) 

        # First option will be disabled.
        if value == options[0].get('value'):
            errors[key].append(toolkit.Invalid('Illegal option selected'))
    else:
        # Second option will be disabled.
        if value == options[1].get('value'):
            errors[key].append(toolkit.Invalid('Illegal option selected'))
