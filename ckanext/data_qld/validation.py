import ckanext.scheming.helpers as sh
from ckantoolkit import missing, Invalid, _, get_validator, request

from ckan.lib.uploader import ALLOWED_UPLOAD_TYPES, _get_underlying_file


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


def read_schema_from_request(key, data, errors, context):
    try:
        request.files
    except TypeError:
        # working outside context, cli or tests
        return data[key]

    if request.files.get("schema_upload") and not data[key]:
        schema_upload = request.files.get("schema_upload")
        data[key] = _get_underlying_file(schema_upload).read()
        return data[key]

    return data[key]


def read_schema_from_file(key, data, errors, context):
    if data[key]:
        return

    schema_upload_key = ("schema_upload",)
    schema_upload = data.get(schema_upload_key)

    if isinstance(schema_upload, ALLOWED_UPLOAD_TYPES) \
        and schema_upload and schema_upload.filename:
        data[schema_upload_key] = ""
        data[key] = _get_underlying_file(schema_upload).read()
