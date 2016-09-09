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
Test for commissaire_http.router
"""

from . import TestCase
from commissaire_http.router import Router

class TestRouter(TestCase):
    """
    Test for the Router class.
    """

    def setUp(self):
        """
        Creates a new instance to test with per test.
        """
        self.router_instance = Router()
        self.router_instance.connect(
            '/path/',
            controller='controller',
            conditions={'method': 'GET'})

    def test_router_successful_match(self):
        """
        Verify the Router finds connected paths.
        """
        self.assertTrue(self.router_instance.match('/path/'))

    def test_router_missing_match(self):
        """
        Verify the Router returns None on unsuccessful match.
        """
        self.assertIsNone(self.router_instance.match('/idonotexist/'))
