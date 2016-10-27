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
Authentication related code for Commissaire.
"""

import logging
import base64


class Authenticator:
    """
    Base class for authentication implementations.
    """

    #: Logger for authenticators
    logger = logging.getLogger('authentication')

    def __init__(self, app):
        """
        Initialize a new instance of Authenticator.

        :param app: A WSGI app to wrap.
        :type app: instance
        """
        self._app = app
        self.__name = self.__class__.__name__

    def __call__(self, environ, start_response):
        """
        WSGI Middleware to inject authentication before the
        requests is processed.

        :param environ: WSGI environment instance.
        :type environ: dict
        :param start_response: WSGI start response callable.
        :type start_response: callable
        :returns: Response back to requestor.
        :rtype: list
        """
        result = self.authenticate(environ, start_response)
        # If the result is True then the authn was successful
        if result is True:
            self.logger.debug('{} successfully authenticated.'.format(
                self.__name))
            return self._app(environ, start_response)
        # If we have a list response then the plugin is handling
        # it's own status code and response body
        elif isinstance(result, list):
            self.logger.debug(
                '{} owned status code and body.'.format(
                    self.__name))
            return result
        # Fall through to a generic forbidden
        self.logger.debug('{} failed authentication.'.format(
            self.__name))
        start_response(
            '403 Forbidden', [('content-type', 'text/html')])
        return [bytes('Forbidden', 'utf8')]

    def authenticate(self, environ, start_response):
        """
        Method should be overriden with a specific authentication
        call for an implementation.

        :param environ: WSGI environment instance.
        :type environ: dict
        :param start_response: WSGI start response callable.
        :type start_response: callable
        :returns: True on success, False on failure
        :rtype: bool
        """
        return False


def decode_basic_auth(logger, http_auth):
    """
    Decodes basic auth from the header string.

    :param logger: logging instance
    :type logger: Logger
    :param http_auth: Basic authentication header
    :type http_auth: string
    :returns: tuple -- (username, passphrase) or (None, None) if empty.
    :rtype: tuple
    """
    if http_auth is not None:
        if http_auth.lower().startswith('basic '):
            try:
                decoded = tuple(base64.decodebytes(
                    http_auth[6:].encode('utf-8')).decode().split(':'))
                if logger:
                    logger.debug('Credentials given: {0}'.format(decoded))
                return decoded
            except base64.binascii.Error:
                if logger:
                    logger.info(
                        'Bad base64 data sent. Setting to no user/pass.')
    # Default meaning no user or password
    return (None, None)
