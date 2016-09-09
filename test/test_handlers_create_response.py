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
Test for commissaire_http.handlers.create_response
"""

from . import TestCase
from commissaire_http.handlers import create_response

UID = '123'


class Test_create_response(TestCase):
    """
    Test for the create_response helper function.
    """

    def test_create_response_without_result_or_error(self):
        """
        Verify create_response requires a result or error.
        """
        self.assertRaises(TypeError, create_response, UID)

    def test_create_response_with_result(self):
        """
        Verify create_response creates the proper result jsonrpc structure.
        """
        response = create_response(UID, result={'test': 'data'})
        self.assertEquals('2.0', response['jsonrpc'])
        self.assertEquals(UID, response['id'])
        self.assertEquals({'test': 'data'}, response['result'])

    def test_create_response_with_error(self):
        """
        Verify create_response creates the proper error jsonrpc structure.
        """
        response = create_response(UID, error='test')
        self.assertEquals('2.0', response['jsonrpc'])
        self.assertEquals(UID, response['id'])
        self.assertEquals('test', response['error']['message'])
