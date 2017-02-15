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
Client certificate authentication plugin.
"""

from commissaire_http.authentication import Authenticator


class HTTPClientCertAuth(Authenticator):
    """
    Requires a client certificate. If a cn
    argument is given it must match the
    cn on any incoming certificate. If cn is
    left blank then client certificate is
    accepted.
    """

    def __init__(self, app, cn=None):
        """
        Initializes an instance of HTTPClientCertAuth.

        :param app: The WSGI application being wrapped with authenticaiton.
        :type app: callable
        :param cn: Optional CommonName to use when checking certificates.
        :type cn: str or None
        """
        super(HTTPClientCertAuth, self).__init__(app)
        self.cn = cn

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
        cert = environ.get('SSL_CLIENT_VERIFY')
        if cert:
            for obj in cert.get('subject', ()):
                for key, value in obj:
                    if key == 'commonName' and \
                            (not self.cn or value == self.cn):
                        return True

        # Forbid by default
        return False


PluginClass = HTTPClientCertAuth
