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
Test cases for the commissaire_http.authentication module.
"""

from unittest import mock

from . import TestCase, create_environ

from commissaire_http import authentication

# The response from dummy_wsgi_app
DUMMY_WSGI_BODY = [bytes('hi', 'utf8')]

def dummy_wsgi_app(environ, start_response):
    return DUMMY_WSGI_BODY


class Test_Authenticator(TestCase):
    """
    Tests for the Authenticator class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.authenticator = authentication.Authenticator(dummy_wsgi_app)

    def test_authenticator_authenticate(self):
        """
        Verify Authenticator's authenticate defaults to forbidden.
        """
        self.assertFalse(self.authenticator.authenticate(
            create_environ(), mock.MagicMock()))

    def test_authenticator_WSGI_interface_default_failure(self):
        """
        Verify Authenticator's WSGI interface properly fails authn by default.
        """
        self.assertEquals([bytes('Forbidden', 'utf8')], self.authenticator(
            create_environ(), mock.MagicMock()))

    def test_authenticator_WSGI_interface_allows_successes(self):
        """
        Verify Authenticator's WSGI interface properly allows authn success.
        """
        self.authenticator.authenticate = mock.MagicMock(return_value=True)
        self.assertEquals(DUMMY_WSGI_BODY, self.authenticator(
            create_environ(), mock.MagicMock()))
