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

import os

from unittest import TestCase, mock

from commissaire_http.handlers import create_jsonrpc_response


def create_environ(path='/', headers={}):
    """
    Shortcut for creating an fake WSGI environ.
    """
    env = {
        'PATH_INFO': path,
    }
    env.update(headers)
    return env


def get_fixture_file_path(filename):
    """
    Attempts to return the path to a fixture file.

    :param filename: The name of the file to look for.
    :type filename: str
    :returns: Full path to the file
    :rtype: str
    :raises: Exception
    """
    for x in ('.', '..'):
        try:
            a_path = os.path.sep.join((x, filename))
            os.stat(a_path)
            return os.path.realpath(a_path)
        except:
            pass
    raise Exception(
        'Can not find path for config: {0}'.format(filename))


def expected_error(message_id, code):
    """
    Creates an expected error structure with the error information as mock.ANY.

    :param message_id: The ID of the message.
    :type message_id: str
    :param code: The JSONRPC_ERRORS code to use.
    :type code: int
    :returns: An error structure for use with tests.
    :rtpe: dict
    """
    expected = create_jsonrpc_response(
        message_id, error='error', error_code=code)
    expected['error'] = mock.ANY
    return expected

class TestCase(TestCase):
    """
    Parent class for all unittests.
    """
    pass
