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
Utilities for CLI.
"""


def parse_to_struct(inp):
    """
    Parses a command line structure into a dictionary creation structure.

    :param inp: The input string from argparse.
    :type inp: str
    :returns: The parsed structure in a pre dictionary format.
    :rtype: list
    """
    name, args = inp.split(':')
    new = {name: {}}
    for item in args.split(','):
        try:
            k, v = item.split('=')
            new[name][k] = v
        except ValueError:
            # Ignore values with out equals
            pass
    return new
