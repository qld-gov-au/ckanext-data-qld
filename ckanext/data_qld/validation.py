from six import string_types
from ckantoolkit import missing, Invalid, _, get_validator, request

from ckan.lib.uploader import ALLOWED_UPLOAD_TYPES, _get_underlying_file

import ckanext.scheming.helpers as sh

OneOf = get_validator('OneOf')


def scheming_validator(fn):
    """
    Decorate a validator that needs to have the scheming fields
    passed with this function. When generating navl validator lists
    the function decorated will be called passing the field
    and complete schema to produce the actual validator for each field.
    """
    fn.is_a_scheming_validator = True
    return fn


@scheming_validator
def scheming_choices(field, schema):
    """
    Require that one of the field choices values is passed.
    """
    if 'choices' in field:
        return OneOf([c['value'] for c in field['choices']])

    def validator(value):
        if value is missing or not value:
            return value
        choices = sh.scheming_field_choices(field)
        for c in choices:
            #  We want the value check to be case insensitive
            if value.upper() == c['value'].upper():
                return value
        raise Invalid(_('unexpected choice "%s"') % value)

    return validator


def process_schema_fields(key, data, errors, context):
    schema_from_upload_request = read_schema_from_request()
    if schema_from_upload_request:
        data[key] = schema_from_upload_request
        return

    schema_from_upload_file = read_schema_from_file(data)
    if schema_from_upload_file:
        data[key] = schema_from_upload_file
        return

    schema_from_url = get_schema_from_url(key, data, errors)
    if schema_from_url:
        data[key] = schema_from_url
        return

    schema_from_json = get_schema_from_json(data)
    if schema_from_json:
        data[key] = schema_from_json
        return


def read_schema_from_request():
    try:
        request.files
    except TypeError:
        # working outside context, cli or tests
        return

    if request.files.get("schema_upload"):
        schema_upload = request.files.get("schema_upload")
        return _get_underlying_file(schema_upload).read()


def read_schema_from_file(data):
    schema_upload_key = ("schema_upload", )
    schema_upload = data.get(schema_upload_key)

    if isinstance(schema_upload, ALLOWED_UPLOAD_TYPES) \
        and schema_upload and schema_upload.filename:
        data[schema_upload_key] = ""
        return _get_underlying_file(schema_upload).read()


def get_schema_from_url(key, data, errors):
    schema_url_key = ("schema_url", )
    value = data.get(schema_url_key)

    if not value:
        return

    if (value and not isinstance(value, string_types)
            or not value.lower()[:4] == u'http'):
        data[schema_url_key] = ""
        err_msg = _('Must be a valid URL "{}"').format(value)
        raise Invalid(err_msg)

    return value


def get_schema_from_json(data):
    schema_json_key = ("schema_json", )
    value = data.get(schema_json_key)

    if value:
        data[schema_json_key] = ""
        return value
