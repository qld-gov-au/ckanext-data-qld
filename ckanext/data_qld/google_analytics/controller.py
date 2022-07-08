# encoding: utf-8

from ckan.controllers.api import ApiController

from . import controller_functions


class GoogleAnalyticsApiController(ApiController):

    def action(self, api_action, ver=None):
        return controller_functions.action(self._get_request_data, ApiController.action, api_action, ver)
