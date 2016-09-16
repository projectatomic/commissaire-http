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
        if self.authenticate(environ, start_response):
            self._app(environ, start_response)
        else:
            start_response('403 Forbidden', [('content-type', 'text/html')])
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
