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
Test for commissaire_http.server
"""

from unittest import mock

from . import TestCase

from commissaire.util.config import ConfigurationError

from commissaire_http.authentication import AuthenticationManager
from commissaire_http.server import cli
from commissaire_http.dispatcher import Dispatcher


class TestServerCli(TestCase):
    """
    Test for the server cli module.
    """

    @mock.patch('commissaire_http.server.cli.DISPATCHER')
    @mock.patch('commissaire_http.server.cli.CommissaireHttpServer')
    def test_main(self, _server, _dispatcher):
        """
        Verify the server is started when main is executed.
        """
        cli.main()
        _server().serve_forever.assert_called_once_with()


class TestInjectAuthentication(TestCase):
    """
    Tests for the cli.inject_authentication function.
    """

    # def tearDown(self):
    #     cli.DISPATCHER.dispatch.authenticators = []

    def test_inject_authentication_with_no_kwargs(self):
        """
        Verify cli.inject_authentication works when no kwargs are given.
        """
        result = cli.inject_authentication({'httpbasicauth': {}})
        self.assertIsInstance(result, Dispatcher)
        self.assertIsInstance(result.dispatch, AuthenticationManager)

    def test_inject_authentication_with_kwargs(self):
        """
        Verify cli.inject_authentication works when kwargs are given.
        """
        result = cli.inject_authentication({
            'httpbasicauth': {
                'filepath': 'conf/users.json',
        }})
        self.assertIsInstance(result, Dispatcher)
        self.assertIsInstance(result.dispatch, AuthenticationManager)

    def test_inject_authentication_with_a_missing_authenticator(self):
        """
        Verify cli.inject_authentication raises when an authenticator doesn't exist.
        """
        self.assertRaises(
            ConfigurationError,
            cli.inject_authentication,
            {'commissaire_http.doesnotexist': {}})
