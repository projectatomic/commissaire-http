# Copyright (C) 2016-2017  Red Hat, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
OpenShift Bearer Token Auth
"""

import requests

from commissaire_http.authentication import Authenticator


class OpenShiftBearerTokenAuth(Authenticator):
    """
    OpenShift Bearer Token auth.
    """

    def __init__(self, openshift_endpoint):
        """
        Authentication using the OpenShift API endpoint and a Bearer token.

        :param openshift_endpoint: The full URI of the endpoint
        :type openshift_endpoint: str
        """
        self.openshift_endpoint = openshift_endpoint

    def check_authentication(self, authorization):
        """
        Checks the user name and password from an Authorization header
        against the OpenShift API.

        :param authorization: Full bearer token value
        :type user: str
        :returns: Whether access is granted
        :rtype: bool
        """
        headers = {
            'Authorization': authorization,
        }
        try:
            resp = requests.get(
                self.openshift_endpoint, headers=headers, verify=False)
            if resp.status_code == 200:
                self.logger.debug(
                    '%s succeeded against the OpenShift endpoint',
                    authorization)
                return True
            self.logger.warn(
                'OpenShift endpoint returned %s', resp.status_code)
        except requests.exceptions.ConnectionError as error:
            self.logger.warn('Unable to authenticate with "%s"', authorization)
            self.logger.debug(
                '%s returned %s',
                self.openshift_endpoint, str(error))
        return False

    def authenticate(self, environ, start_response):
        """
        Implements the authentication logic.

        :param environ: WSGI environment instance.
        :type environ: dict
        :param start_response: WSGI start response callable.
        :type start_response: callable
        :returns: True on success, False on failure
        :rtype: bool
        """
        authorization = environ.get('Authorization')

        # Return out fast if the header isn't there or is empty
        if not authorization:
            self.logger.debug('Bearer token was missing')
            return False

        # Return if the header doesn't start with bearer:
        if not authorization.lower().startswith('bearer:'):
            self.logger.debug('Authorization header missing bearer:')
            return False

        if self.check_authentication(authorization):
            return True  # Authentication is good

        self.logger.debug('%s is an invalid bearer token', authorization)
        # Forbid by default
        return False


PluginClass = OpenShiftBearerTokenAuth
