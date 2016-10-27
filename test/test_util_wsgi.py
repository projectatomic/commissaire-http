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
Test cases for the commissaire_http.util.wsgi module.
"""

from . import TestCase

from commissaire_http.util import wsgi


class Test_AuthenticationManager(TestCase):
    """
    Tests for the AuthenticationManager class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.fake_start_response = wsgi.FakeStartResponse()

    def test_fake_start_response_call_count(self):
        """
        Verify FakeStartResponse holds the correct call count.
        """
        for x in range(1, 11):
            self.fake_start_response('200 OK', [])
            self.assertEquals(x, self.fake_start_response.call_count)

    def test_fake_start_response_stores_code_and_headers(self):
        """
        Verify FakeStartResponse holds the latest code and headers.
        """
        test_args = [
            ('200 OK', ()),
            ('403 Forbidden', (('content-type', 'text/html')))]

        for args in test_args:
            self.fake_start_response(*args)
            # Each iteration should match the latest
            self.assertEquals(
                args[0],
                self.fake_start_response.code)
            self.assertEquals(
                args[1],
                self.fake_start_response.headers)

        # The end result should ONLY be the latest
        self.assertEquals(
            test_args[-1][0],
            self.fake_start_response.code)
        self.assertEquals(
            test_args[-1][1],
            self.fake_start_response.headers)
