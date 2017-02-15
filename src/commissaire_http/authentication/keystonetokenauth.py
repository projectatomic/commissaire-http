# Copyright (C) 2016  Red Hat, Inc
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
OpenStack Keystone authentication plugin.
"""

import json
import requests

from commissaire_http.authentication import Authenticator


class KeystoneToken(Authenticator):
    """
    Auth implementation using token method against OpenStack Keystone
    """

    def __init__(self, app, url=None):
        """
        Checks the token given as the X-Auth-Token header
        against the specified OpenStack Keystone instance
        :param app: The WSGI application being wrapped with authenticaiton.
        :type app: callable
        :param url: The OpenStack Keystone endpoint used for Authentication
        :type url: string
        :returns
        """
        super(KeystoneToken, self).__init__(app)
        self.url = url

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
        token = environ.get('HTTP_X_AUTH_TOKEN')
        if not token:
            return False

        headers = {'Content-Type': 'application/json'}
        body = {'auth': {'identity': {}}}
        ident = body['auth']['identity']

        ident['methods'] = ['token']
        ident['token'] = {'id': token}

        try:
            response = requests.post(
                self.url,
                data=json.dumps(body),
                headers=headers)
        except requests.exceptions.BaseHTTPError as error:
            self.logger.error('Could not reach {}. Denying access. {}: {}'
                              .format(self.url, type(error), error))
            return False

        subject_token_name = 'X-Subject-Token'
        if subject_token_name in response.headers:
            token = response.headers[subject_token_name]
            start_response('200 OK', [
                           ('content-type', 'application/json'),
                           (subject_token_name, token)])
            return True

        # Forbid by default
        return False


PluginClass = KeystoneToken
