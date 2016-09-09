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
Test for commissaire_http.dispatcher.parse_query_string
"""

from . import TestCase
from commissaire_http.dispatcher import parse_query_string


class Test_parse_query_string(TestCase):
    """
    Test for the parse_query_string helper function.
    """

    def Test_parse_query_string_with_unescaped_data(self):
        """
        Verify parse_query_string works when no data has to be escaped.
        """
        self.assertEquals(
            {'test': 'ok'},
            parse_query_string('test=ok'))
        self.assertEquals(
            {'test': 'ok', 'second': 'item'},
            parse_query_string('test=ok&second=item'))
        self.assertEquals(
            {'test': ['ok', 'another'], 'second': 'item'},
            parse_query_string('test=ok&second=item&test=another'))


    def Test_parse_query_string_with_escaped_data(self):
        """
        Verify parse_query_string works when data has to be escaped.
        """
        self.assertEquals(
            {'test': '&quot;ok&quot;'},
            parse_query_string('test="ok"'))
        self.assertEquals(
            {'test': '&quot;ok&quot;', 'second': 'item'},
            parse_query_string('test="ok"&second=item'))
        self.assertEquals(
            {'test': ['&quot;ok&quot;', 'another'], 'second': 'item'},
            parse_query_string('test="ok"&second=item&test=another'))
