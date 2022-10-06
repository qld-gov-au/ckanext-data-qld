import json
from six import string_types

import ckan.plugins.toolkit as tk
from ckan.lib.uploader import _get_underlying_file

import ckanext.scheming.helpers as sh
from ckanext.validation.helpers import is_url_valid

import ckanext.data_qld.constants as const
from ckanext.data_qld.helpers import is_uploaded_file, is_ckan_29
from ckanext.data_qld.utils import is_api_call


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
        OneOf = tk.get_validator('OneOf')

        return OneOf([c['value'] for c in field['choices']])

    def validator(value):
        if value is tk.missing or not value:
            return value
        choices = sh.scheming_field_choices(field)
        for c in choices:
            #  We want the value check to be case insensitive
            if value.upper() == c['value'].upper():
                return value
        raise tk.Invalid(tk._('unexpected choice "%s"') % value)

    return validator


def process_schema_fields(key, data, errors, context):
    schema_from_upload_request = read_schema_from_request()

    if schema_from_upload_request:
        data[key] = schema_from_upload_request
        _clear_pseudo_fields(data)
        return

    schema_from_upload_file = read_schema_from_file(data)
    if schema_from_upload_file:
        data[key] = schema_from_upload_file
        _clear_pseudo_fields(data)
        return

    schema_from_url = get_schema_from_url(key, data, errors)
    if schema_from_url:
        data[key] = schema_from_url
        _clear_pseudo_fields(data)
        return

    schema_from_json = get_schema_from_json(data)
    if schema_from_json:
        data[key] = schema_from_json
        _clear_pseudo_fields(data)
        return


def read_schema_from_request():
    try:
        if is_ckan_29():
            form_data = tk.request.files
        else:
            form_data = tk.request.params
    except TypeError:
        # working outside context, cli or tests
        return

    shema_upload = form_data.get(const.FIELD_SCHEMA_UPLOAD)

    if is_uploaded_file(shema_upload):
        schema_upload = form_data.get(const.FIELD_SCHEMA_UPLOAD)
        return _get_underlying_file(schema_upload).read()


def read_schema_from_file(data):
    schema_upload_key = (const.FIELD_SCHEMA_UPLOAD, )
    schema_upload = data.get(schema_upload_key)

    if is_uploaded_file(schema_upload):
        data[schema_upload_key] = ""
        return _get_underlying_file(schema_upload).read()


def get_schema_from_url(key, data, errors):
    schema_url_key = (const.FIELD_SCHEMA_URL, )
    value = data.get(schema_url_key)

    if not value:
        return

    if (value and not isinstance(value, string_types)
            or not is_url_valid(value)):
        data[schema_url_key] = ""
        err_msg = tk._('Must be a valid URL "{}"').format(value)
        raise tk.Invalid(err_msg)

    return value


def get_schema_from_json(data):
    schema_json_key = (const.FIELD_SCHEMA_JSON, )
    value = data.get(schema_json_key)

    if value:
        data[schema_json_key] = ""
        return value


def _clear_pseudo_fields(data):
    schema_json_key = (const.FIELD_SCHEMA_JSON, )
    schema_url_key = (const.FIELD_SCHEMA_URL, )
    schema_upload_key = (const.FIELD_SCHEMA_UPLOAD, )

    data[schema_json_key] = data[schema_url_key] = data[schema_upload_key] = ""


def align_default_schema(key, data, errors, context):
    """Align resource schema with package schema"""
    if not data[key]:
        return

    if context.get("ignore_auth"):
        return

    # key = ('resources', 0, 'align_default_schema')
    if len(key) != 3 or key[2] != const.FIELD_ALIGNMENT:
        return

    default_schema = data[(const.FIELD_DEFAULT_SCHEMA, )]
    resource_idx = key[1]
    resource_schema_key = (const.FIELD_RESOURCES, resource_idx,
                           const.FIELD_RES_SCHEMA)
    resource_schema = data[resource_schema_key]
    resource_id = data.get((const.FIELD_RESOURCES, resource_idx, 'id'))

    if resource_id and _is_already_aligned(resource_id, resource_schema,
                                           context):
        return

    if not default_schema:
        raise tk.Invalid(tk._("Missing {}").format(const.FIELD_DEFAULT_SCHEMA))

    if resource_schema == default_schema:
        return

    if is_api_call():
        errors[key].append(tk._("This field couldn't be updated via API"))
        raise tk.StopOnError()

    data[resource_schema_key] = default_schema


def _is_already_aligned(resource_id, resource_schema, context):
    model = context['model']
    session = context['session']

    resource = session.query(model.Resource).get(resource_id)

    alignment_value = resource.extras.get(const.FIELD_ALIGNMENT)
    schema = resource.extras.get(const.FIELD_RES_SCHEMA)

    if is_url_valid(schema):
        schemas_aligned = schema == resource_schema
    else:
        schemas_aligned = json.loads(schema) == resource_schema

    return all([bool(alignment_value), schemas_aligned])


def check_schema_alignment(key, data, errors, context):
    """If resource and package schemes are different set `align_default_schema` to False"""
    default_schema = data.get((const.FIELD_DEFAULT_SCHEMA, ))

    resource_schema = data[key]
    resource_idx = key[1]

    alignment_value = const.ALIGNED if (default_schema and resource_schema
                                        == default_schema) else const.UNALIGNED
    data[(const.FIELD_RESOURCES, resource_idx,
          const.FIELD_ALIGNMENT)] = alignment_value
