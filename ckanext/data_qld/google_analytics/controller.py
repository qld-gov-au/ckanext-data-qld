# encoding: utf-8

from ckan.controllers.api import ApiController
from ckantoolkit import get_action

from controller_functions import record_api_action


class GoogleAnalyticsApiController(ApiController):

    def action(self, api_action, ver=None):
        function = get_action(api_action)
        side_effect_free = getattr(function, 'side_effect_free', False)
        request_data = self._get_request_data(try_url_params=side_effect_free)
        record_api_action(api_action, request_data)
        return ApiController.action(self, api_action, ver)
