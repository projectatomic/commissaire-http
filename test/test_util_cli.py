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
Test cases for the commissaire_http.util.cli module.
"""

from . import TestCase

from commissaire_http.util import cli


class Test_parse_to_struct(TestCase):
    """
    Tests for the parse_to_struct function
    """

    def test_parse_to_struct_with_class_only(self):
        """
        Verify parse_to_struct creates a proper struct with only a class name.
        """
        self.assertEquals(
            {'someclass': {}},
            cli.parse_to_struct('someclass:'))

    def test_parse_to_struct_with_class_and_args(self):
        """
        Verify parse_to_struct creates a proper struct with a class and args.
        """
        self.assertEquals(
            {'someclass': {'k': 'v', 'a': 'b'}},
            cli.parse_to_struct('someclass:k=v,a=b'))

    def test_parse_to_struct_ignore_unparsable_args(self):
        """
        Verify parse_to_struct ignores unparsable items in args.
        """
        self.assertEquals(
            {'someclass': {'k': 'v'}},
            cli.parse_to_struct('someclass:k=v,IDONOTBELONG'))
