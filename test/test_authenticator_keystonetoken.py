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
Test cases for the commissaire_http.authentication.keystonetokenauth module.
"""

import requests

from . import TestCase, create_environ

from unittest import mock

from commissaire_http.authentication import keystonetokenauth


# Reusable environ for tests
TOKEN = '69120179c8e747e3ae8c68c00ec56eb6'
ENVIRON = create_environ(
    headers={'HTTP_X_AUTH_TOKEN': TOKEN})

# Reusable keystone success response
SUCCESS_RESPONSE = requests.Response()
SUCCESS_RESPONSE.headers['X-Subject-Token'] = TOKEN

# Reusable keystone failure response
FAILURE_RESPONSE = requests.Response()


class TestKeystoneToken(TestCase):
    """
    Tests for the KeystoneToken class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.keystone_token_auth = keystonetokenauth.KeystoneToken(
            None, 'https://example.com/v3/auth/tokens')

    def test_authenticate_with_valid_token(self):
        """
        Keystone Token: Verify a valid token authenticates successfully.
        """
        # patch the post function
        with mock.patch('requests.post') as _post:
            # Define what the response should be from post
            _post.return_value = SUCCESS_RESPONSE

            # Run the authenticate method
            result = self.keystone_token_auth.authenticate(
                ENVIRON, mock.MagicMock())
            # True means successful authn
            self.assertTrue(result)

    def test_authenticate_with_invalid_token(self):
        """
        Keystone Token: Verify an invalid token fails authentication.
        """
        # patch the post function
        with mock.patch('requests.post') as _post:
            # The response should not have a token
            _post.return_value = FAILURE_RESPONSE

            # Run the authenticate method
            result = self.keystone_token_auth.authenticate(
                ENVIRON, mock.MagicMock())
            # True means successful authn
            self.assertFalse(result)

    def test_authenticate_with_invalid_data(self):
        """
        Keystone Token: Verify missing data does not successfully allow authentication.
        """
        with mock.patch('requests.post') as _post:
            # We give the response a token even though it should never get
            # to this point as the initial data is invalid. If it does get
            # the token then authentication succeeds and we know it's a
            # test failure
            _post.return_value = SUCCESS_RESPONSE

            # Run the authenticate method without HTTP_X_AUTH_TOKEN
            result = self.keystone_token_auth.authenticate(
                create_environ(), mock.MagicMock())
            # True means successful authn
            self.assertFalse(result)
