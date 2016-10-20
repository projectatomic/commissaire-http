"""
OpenStack Keystone authentication plugin.
"""

import json
import requests

from commissaire_http.authentication import Authenticator
from commissaire_http.authentication import decode_basic_auth


class KeystonePassword(Authenticator):
    """
    Auth implementation using password method against OpenStack Keystone
    """

    def __init__(self, app, url=None, domain='Default'):
        """
        Checks the user name and password from an Authorization header
        against the specified OpenStack Keystone instance

        :param app: The WSGI application being wrapped with authenticaiton.
        :type app: callable
        :param url: The OpenStack Keystone endpoint used for Authentication
        :type url: string
        :returns: HTTPBasicAuth
        """
        super(KeystonePassword, self).__init__(app)
        self.url = url
        self.domain = domain

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
        user, passwd = decode_basic_auth(
            self.logger,
            environ.get('HTTP_AUTHORIZATION'))

        headers = {'Content-Type': 'application/json'}
        body = {'auth': {'identity': {}}}
        ident = body['auth']['identity']

        ident['methods'] = ['password']
        ident['password'] = {'user': {
            'name': user,
            'password': passwd,
            'domain': {'name': self.domain}}}

        response = requests.post(
            self.url,
            data=json.dumps(body),
            headers=headers)

        if 'X-Subject-Token' in response.headers:
            return True

        # Forbid by default
        return False


AuthenticationPlugin = KeystonePassword
