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
Test cases for the commissaire_http.authentication.keystonepasswordauth module.
"""

import requests

from . import TestCase, create_environ

from unittest import mock

from commissaire_http.authentication import decode_basic_auth
from commissaire_http.authentication import httpbasicauth
from commissaire_http.authentication import keystonepasswordauth


# Reusable environ for tests
ENVIRON = create_environ(
    headers={'HTTP_AUTHORIZATION': 'basic YTph'})

# Reusable keystone success response
SUCCESS_RESPONSE = requests.Response()
SUCCESS_RESPONSE.headers['X-Subject-Token'] = 'token'

# Reusable keystone failure response
FAILURE_RESPONSE = requests.Response()


class TestKeystonePassword(TestCase):
    """
    Tests for the KeystonePassword class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.keystone_password_auth = keystonepasswordauth.KeystonePassword(
            None, 'https://example.com/v3/auth/tokens', 'Default')

    def test_authenticate_with_valid_user(self):
        """
        Verify a valid user authenticates successfully.
        """
        # patch the post function
        with mock.patch('requests.post') as _post:
            # Define what the response should be from post
            _post.return_value = SUCCESS_RESPONSE

            # Run the authenticate method
            result = self.keystone_password_auth.authenticate(
                ENVIRON, mock.MagicMock())
            # True means successful authn
            self.assertTrue(result)

    def test_authenticate_with_invalid_user(self):
        """
        Verify an invalid user fails authentication.
        """
        # patch the post function
        with mock.patch('requests.post') as _post:
            # The response should not have a token
            _post.return_value = FAILURE_RESPONSE

            # Run the authenticate method
            result = self.keystone_password_auth.authenticate(
                ENVIRON, mock.MagicMock())
            # True means successful authn
            self.assertFalse(result)

    def test_authenticate_with_invalid_data(self):
        """
        Verify missing data does not successfully allow authentication.
        """
        with mock.patch('requests.post') as _post:
            # We give the response a token even though it should never get
            # to this point as the initial data is invalid. If it does get
            # the token then authentication succeeds and we know it's a
            # test failure
            _post.return_value = SUCCESS_RESPONSE

            # Run the authenticate method without HTTP_AUTHORIZATION
            result = self.keystone_password_auth.authenticate(
                create_environ(), mock.MagicMock())
            # True means successful authn
            self.assertFalse(result)
