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
Test cases for
commissaire_http.authentication.openshiftbearertokenauth.PluginClass
"""

import requests

from . import TestCase, create_environ

from unittest import mock

from commissaire_http.authentication.openshiftbearertokenauth import (
    OpenShiftBearerTokenAuth)


# Reusable environ for tests
TOKEN = '123456789012345678901234567890'
ENVIRON = create_environ(
    headers={'Authorization': 'BEARER: {}'.format(TOKEN)})

# Reusable success response
SUCCESS_RESPONSE = requests.Response()
SUCCESS_RESPONSE.status_code = 200

# Reusable failure response
FAILURE_RESPONSE = requests.Response()
FAILURE_RESPONSE.status_code = 403


class TestOpenShiftBearerTokenAuth(TestCase):
    """
    Tests for the OpenShiftBearerTokenAuth class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.os_bearer_token_auth = OpenShiftBearerTokenAuth(
            'https://example.com/v3/auth/tokens')

    def test_authenticate_with_valid_token(self):
        """
        Verify a valid token authenticates successfully.
        """
        # patch the post function
        with mock.patch('requests.get') as _get:
            # Define what the response should be from get
            _get.return_value = SUCCESS_RESPONSE

            # Run the authenticate method
            result = self.os_bearer_token_auth.authenticate(
                ENVIRON, mock.MagicMock())
            self.assertTrue(result)

    def test_authenticate_with_invalid_token(self):
        """
        Verify an invalid token fails authentication.
        """
        # patch the post function
        with mock.patch('requests.get') as _get:
            # The response should not have a token
            _get.return_value = FAILURE_RESPONSE

            # Run the authenticate method
            result = self.os_bearer_token_auth.authenticate(
                ENVIRON, mock.MagicMock())
            self.assertFalse(result)

    def test_authenticate_with_missing_data(self):
        """
        Verify missing data does not successfully allow authentication.
        """
        with mock.patch('requests.get') as _get:
            # The response should not have a token
            _get.return_value = FAILURE_RESPONSE

            # We give the response a token even though it should never get
            # to this point as the initial data is invalid. If it does get
            # the token then authentication succeeds and we know it's a
            # test failure
            _get.return_value = FAILURE_RESPONSE

            # Run the authenticate method without Authorization
            result = self.os_bearer_token_auth.authenticate(
                create_environ(), mock.MagicMock())
            self.assertFalse(result)
