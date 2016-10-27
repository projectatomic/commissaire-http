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
WSGI utilities.
"""


class FakeStartResponse:
    """
    A fake start_response implementation that stores the input given.
    """

    def __init__(self):
        """
        Initializes a new FakeStartResponse.
        """
        self.call_count = 0
        self.code = ''
        self.headers = ()

    def __call__(self, code, headers):
        """
        Executed when the start_response "function" is called.

        :param code: The status code that would normally be returned.
        :type code: str
        :param headers: Headers that would normally be sent.
        :type headers: tuple
        """
        self.call_count += self.call_count
        self.code = code
        self.headers = headers

    def __repr__(self):  # noqa
        """
        Unambiguous representation of the instance.
        """
        return ('<FakeStartResponse: call_count={}, '
                'code={}, headers={}>').format(
                    self.call_count, self.code, self.headers)

    def __str__(self):  # noqa
        """
        Readable representation of the instance.
        """
        return 'call_count={}, code={}, headers={}'.format(
            self.call_count, self.code, self.headers)
