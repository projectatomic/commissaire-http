# Copyright (C) 2017  Red Hat, Inc
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
Test for commissaire_http.handlers.BasicHandler
"""

from io import BytesIO

from . import TestCase, mock

from commissaire_http.handlers import get_params


class Test_get_params(TestCase):
    """
    Test for the get_params helper function.
    """

    def test_get_params_with_uri_param(self):
        """
        Verify get_params returns proper parameters from a uri.
        """
        route_dict = {
            'test': 'test',
            'controller': 'testing',
        }
        route = mock.MagicMock(minkeys=['test'])
        environ = {
            'PATH_INFO': '/test/',
            'REQUEST_METHOD': 'GET',

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), route_dict),
            'routes.route': route
        }
        self.assertEquals(
            {'test': 'test'},
            get_params(environ))

    def test_get_params_with_query_string(self):
        """
        Verify get_params returns proper parameters from a query string.
        """
        route_dict = {
            'controller': 'testing',
        }
        route = mock.MagicMock(minkeys=[])
        environ = {
            'PATH_INFO': '/test/',
            'QUERY_STRING': 'from=querystring',
            'REQUEST_METHOD': 'GET',

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), route_dict),
            'routes.route': route
        }
        self.assertEquals(
            {'from': 'querystring'},
            get_params(environ))

    def test_get_params_with_wsgi_input(self):
        """
        Verify get_params returns proper parameters from wsgi.input.
        """
        route_dict = {
            'controller': 'testing',
        }
        route = mock.MagicMock(minkeys=[])
        environ = {
            'PATH_INFO': '/test/',
            'REQUEST_METHOD': 'PUT',
            'CONTENT_LENGTH': 16,
            'wsgi.input': BytesIO(b'{"from": "wsgi"}'),

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), route_dict),
            'routes.route': route
        }
        self.assertEquals(
            {'from': 'wsgi'},
            get_params(environ))
