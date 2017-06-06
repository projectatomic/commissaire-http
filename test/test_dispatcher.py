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
Test for commissaire_http.dispatcher
"""

import json

from io import BytesIO

from . import TestCase, mock

import commissaire_http.handlers

from commissaire_http.bus import Bus
from commissaire_http.dispatcher import Dispatcher
from commissaire_http.router import Router


class TestDispatcher(TestCase):
    """
    Test for the Dispatcher class.
    """

    def setUp(self):
        """
        Creates a new instance to test with per test.
        """
        self.router_instance = Router()
        self.router_instance.connect(
            '/hello/',
            controller='commissaire_http.handlers.hello_world',
            conditions={'method': 'GET'})
        self.router_instance.connect(
            '/world/',
            controller='commissaire_http.handlers.create_world',
            conditions={'method': 'PUT'})
        self.dispatcher_instance = Dispatcher(
            self.router_instance,
            handler_packages=['commissaire_http.handlers'])
        self.dispatcher_instance._bus = mock.MagicMock('Bus')

    def test_dispatcher_initialization(self):
        """
        Verify the Dispatcher initializes properly.
        """
        self.assertEquals(
            self.router_instance, self.dispatcher_instance._router)
        self.assertTrue(self.dispatcher_instance._handler_map)

    def test_dispatcher_reload_handlers(self):
        """
        Verify the Dispatcher.reload_handlers actually loads handlers.
        """
        self.dispatcher_instance._handler_map = {}
        self.assertFalse(self.dispatcher_instance._handler_map)
        self.dispatcher_instance.reload_handlers()
        self.assertTrue(self.dispatcher_instance._handler_map)

    def test_dispatcher_dispatch_with_valid_path(self):
        """
        Verify the Dispatcher.dispatch works with valid paths.
        """
        match = {'controller': commissaire_http.handlers.hello_world}
        route = mock.MagicMock(minkeys=[])
        environ = {
            'PATH_INFO': '/hello/',
            'REQUEST_METHOD': 'GET',

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), match),
            'routes.route': route
        }
        start_response = mock.MagicMock()
        result = self.dispatcher_instance.dispatch(environ, start_response)
        start_response.assert_called_once_with('200 OK', mock.ANY)
        self.assertEquals('{"Hello": "there"}', result[0].decode())

    def test_dispatcher_dispatch_with_valid_path_and_params(self):
        """
        Verify the Dispatcher.dispatch works with valid paths and params.
        """
        match = {'controller': commissaire_http.handlers.hello_world}
        route = mock.MagicMock(minkeys=[])
        environ = {
            'PATH_INFO': '/hello/',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': 'name=bob',

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), match),
            'routes.route': route
        }
        start_response = mock.MagicMock()
        result = self.dispatcher_instance.dispatch(environ, start_response)
        start_response.assert_called_once_with('200 OK', mock.ANY)
        self.assertEquals('{"Hello": "bob"}', result[0].decode())

    def test_dispatcher_dispatch_with_valid_path_with_wsgi_input(self):
        """
        Verify the Dispatcher.dispatch works when wsgi_input is in use.
        """
        match = {'controller': commissaire_http.handlers.create_world}
        route = mock.MagicMock(minkeys=[])
        environ = {
            'PATH_INFO': '/world/',
            'REQUEST_METHOD': 'PUT',  # PUT uses wsgi.input
            'wsgi.input': BytesIO(b'{"name": "world"}'),
            'CONTENT_LENGTH': b'18',

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), match),
            'routes.route': route
        }
        start_response = mock.MagicMock()
        result = self.dispatcher_instance.dispatch(environ, start_response)
        start_response.assert_called_once_with('201 Created', mock.ANY)
        self.assertEquals('world', json.loads(result[0].decode())['name'])

    def test_dispatcher_dispatch_with_invalid_path(self):
        """
        Verify the Dispatcher.dispatch works with invalid paths.
        """
        environ = {
            'PATH_INFO': '/idonotexist/',
            'REQUEST_METHOD': 'GET',

            # RoutesMiddleware inserts this.
            'routes.route': None
        }
        start_response = mock.MagicMock()
        result = self.dispatcher_instance.dispatch(environ, start_response)
        start_response.assert_called_once_with('404 Not Found', mock.ANY)
        self.assertEquals('Not Found', result[0].decode())
