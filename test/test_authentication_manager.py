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
Test cases for the commissaire_http.authentication.AuthenticationManager class.
"""

from unittest import mock

from . import TestCase, create_environ

from commissaire_http import authentication

# The response from dummy_wsgi_app
DUMMY_WSGI_BODY = [bytes('hi', 'utf8')]

# Dummy wsgi app for testing
def dummy_wsgi_app(environ, start_response):
    start_response('200 OK', [])
    return DUMMY_WSGI_BODY


class Test_AuthenticationManager(TestCase):
    """
    Tests for the AuthenticationManager class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.authenticator = authentication.Authenticator(dummy_wsgi_app)
        self.authentication_manager = authentication.AuthenticationManager(
            dummy_wsgi_app,
            authenticators=[self.authenticator])

    def test_authentication_manager_simple_deny(self):
        """
        Verify AuthenticationManager handles the simple forbidden case.
        """
        start_response = mock.MagicMock()
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals([bytes('Forbidden', 'utf8')], result)
        start_response.assert_called_once_with('403 Forbidden', mock.ANY)

    def test_authentication_manager_simple_allow(self):
        """
        Verify AuthenticationManager handles the simple allow case.
        """
        start_response = mock.MagicMock()
        self.authenticator.authenticate = mock.MagicMock(return_value=True)
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals(DUMMY_WSGI_BODY, result)
        start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_authenticator_manager_complex_failure(self):
        """
        Verify AuthenticationManager handles the complex forbidden case.
        """
        body = [bytes('test', 'utf8')]
        start_response = mock.MagicMock()
        sr_args = ('403 Forbidden', [])

        # Override the authenticators authenticate with a complex failure
        def authenticate(_, sr):
            sr(*sr_args)
            return body

        self.authenticator.authenticate = authenticate
        self.assertEquals(body, self.authenticator(
            create_environ(), start_response))
        start_response.assert_called_once_with(*sr_args)

    def test_authenticator_manager_complex_success(self):
        """
        Verify AuthenticationManager handles the complex success case.
        """
        start_response = mock.MagicMock()
        sr_args = ('200 OK', [])

        # Override the authenticators authenticate with a complex success
        def authenticate(_, sr):
            sr(*sr_args)
            return []  # Ignored

        self.authenticator.authenticate = authenticate
        self.assertEquals(DUMMY_WSGI_BODY, self.authenticator(
            create_environ(), start_response))
        start_response.assert_called_once_with(*sr_args)

    def test_authentication_manager_multi_simple_deny(self):
        """
        Verify AuthenticationManager handles the simple forbidden case with multiple authenticators.
        """
        start_response = mock.MagicMock()
        self.authentication_manager.authenticators.append(self.authenticator)
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals([bytes('Forbidden', 'utf8')], result)
        start_response.assert_called_once_with('403 Forbidden', mock.ANY)

    def test_authentication_manager_multi_simple_allow(self):
        """
        Verify AuthenticationManager handles the simple allow case with multiple authenticators.
        """
        start_response = mock.MagicMock()
        self.authentication_manager.authenticators = [
            mock.MagicMock(authenticate=mock.MagicMock(return_value=False)),
            mock.MagicMock(authenticate=mock.MagicMock(return_value=True)),
        ]
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals(DUMMY_WSGI_BODY, result)
        start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_authentication_manager_multi_complex_deny(self):
        """
        Verify AuthenticationManager handles the complex forbidden case with multiple authenticators.
        """
        start_response = mock.MagicMock()
        response_code = '402 Payment Required'
        expected_result = [bytes('$$$', 'utf8')]
        def complex_auth(environ, start_response):
            start_response(response_code, [])
            return expected_result

        self.authentication_manager.authenticators = [
            mock.MagicMock(authenticate=mock.MagicMock(return_value=False)),
            mock.MagicMock(authenticate=complex_auth),
            mock.MagicMock(authenticate=mock.MagicMock(return_value=False)),
        ]
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals(expected_result, result)
        start_response.assert_called_once_with(response_code, mock.ANY)

    def test_authentication_manager_multi_complex_allow(self):
        """
        Verify AuthenticationManager handles the complex allow case with multiple authenticators.
        """
        expected_result = [bytes('itrustyou', 'utf8')]
        def complex_auth(environ, start_response):
            start_response('200 OK', [])
            return expected_result

        start_response = mock.MagicMock()
        self.authentication_manager.authenticators = [
            mock.MagicMock(authenticate=mock.MagicMock(return_value=False)),
            mock.MagicMock(authenticate=complex_auth),
            mock.MagicMock(authenticate=mock.MagicMock(return_value=False)),
        ]
        result = self.authentication_manager(create_environ(), start_response)
        self.assertEquals(expected_result, result)
        start_response.assert_called_once_with('200 OK', mock.ANY)
