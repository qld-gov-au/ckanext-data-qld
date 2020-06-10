import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.plugins as plugins
import json
import logging

import constants

from ckan.common import _, g
from ckan.controllers.package import PackageController
from ckan.logic import get_action, NotFound, NotAuthorized

abort = base.abort
log = logging.getLogger(__name__)
tk = plugins.toolkit
c = tk.c


def _get_errors_summary(errors):
    errors_summary = ''

    for key, error in errors.items():
        errors_summary = ', '.join(error)

    return errors_summary


class DataQldUI(base.BaseController):

    def _get_context(self):
        return {'model': model, 'session': model.Session,
                'user': c.user, 'auth_user_obj': c.userobj}

    def open_datarequest(self, id):
        data_dict = {'id': id}
        context = self._get_context()

        # Basic intialization
        c.datarequest = {}
        try:
            tk.check_access(constants.OPEN_DATAREQUEST, context, data_dict)
            c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

            if c.datarequest.get('closed', False) is False:
                tk.abort(403, tk._('This data request is already open'))
            else:
                data_dict = {}
                data_dict['id'] = id
                data_dict['organization_id'] = c.datarequest.get('organization_id')

                tk.get_action(constants.OPEN_DATAREQUEST)(context, data_dict)
                tk.redirect_to(
                    helpers.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                                    action='show', id=data_dict['id']))
        except tk.ValidationError as e:
            log.warn(e)
            errors_summary = _get_errors_summary(e.error_dict)
            tk.abort(403, errors_summary)
        except tk.ObjectNotFound as e:
            log.warn(e)
            tk.abort(404, tk._('Data Request %s not found') % id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to open the Data Request %s' % id))

    def show_schema(self, dataset_id, resource_id):
        data_dict = {'id': resource_id}
        context = self._get_context()

        try:
            tk.check_access(constants.RESOURCE_SHOW, context, data_dict)
            resource = tk.get_action(constants.RESOURCE_SHOW)(context, data_dict)
            schema_data = resource.get('schema')
            c.schema_data = json.dumps(schema_data, indent=2, sort_keys=True)
            return tk.render('schema/show.html')
        except tk.ObjectNotFound as e:
            tk.abort(404, tk._('Resource %s not found') % resource_id)
        except tk.NotAuthorized as e:
            log.warn(e)
            tk.abort(403, tk._('You are not authorized to view the Data Scheme for the resource %s' % resource_id))


class DataQldDataset(PackageController):
    def _get_context(self):
        return {'model': model, 'session': model.Session,
                       'user': c.user, 'for_view': True,
                       'auth_user_obj': c.userobj}

    def _is_dataset_private(self, id):
        try:
            get_action('package_show')(self._get_context(), {'id': id})
            return True
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            return False

    def read(self, id):
        """
        Override the default CKAN behaviour for private Dataset visibility for unauthenticated users.
        Instead of displaying "404 Dataset not found" message, give unauthenticated users a chance to login (if the
        dataset exists but is private).
        :param id: Package id/name
        :return:
        """
        if not g.user and not self._is_dataset_private(id):
            tk.redirect_to(
                tk.url_for('user.login', came_from='/dataset/{id}'.format(id=id))
            )

        return super(DataQldDataset, self).read(id)

    def resource_read(self, id, resource_id):
        """
        Override the default CKAN behaviour for private Dataset Resource visibility for unauthenticated users.
        Instead of displaying "404 Dataset not found" message, give unauthenticated users a chance to login (if the
        dataset exists but is private).
        :param id: Package id/name
        :param resource_id: Resource id
        :return:
        """
        if not g.user and not self._is_dataset_private(id):
            tk.redirect_to(
                tk.url_for('user.login',
                           came_from='/dataset/{id}/resource/{resource_id}'.format(id=id, resource_id=resource_id))
            )

        return super(DataQldDataset, self).resource_read(id, resource_id)
