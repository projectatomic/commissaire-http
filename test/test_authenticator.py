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


class Test_Authenticator(TestCase):
    """
    Tests for the Authenticator class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.authenticator = authentication.Authenticator(None)

    def test_authenticator_authenticate(self):
        """
        Verify Authenticator's authenticate defaults to forbidden.
        """
        self.assertFalse(self.authenticator.authenticate(
            create_environ(), mock.MagicMock()))
