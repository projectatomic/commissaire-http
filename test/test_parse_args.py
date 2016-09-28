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
Test for commissaire_http.parse_args
"""

import sys

from argparse import ArgumentParser

from . import TestCase

from commissaire_http import Namespace, parse_args


class TestParseArgs(TestCase):
    """
    Test for the parse_args function.
    """

    def setUp(self):
        """
        Create a parser for each test and clear args.
        """
        self.parser = ArgumentParser()
        sys.argv = ['']

    def test_parse_args(self):
        """
        Verify parse_args works properly.
        """
        sys.argv.append('--bus-exchange=test')
        ns = parse_args(self.parser)
        self.assertIs(Namespace, type(ns))
        self.assertEquals('test', ns.bus_exchange)
