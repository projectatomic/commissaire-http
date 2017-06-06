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
Test for commissaire_http.handlers.JSONRPC_Handler.
"""

from . import TestCase, mock

from commissaire import constants as C
from commissaire_http.handlers import JSONRPC_Handler


class Test_JSONRPC_Handler(TestCase):
    """
    Test for the JSONRPC_Handler decorator class.
    """

    def setUp(self):
        """
        Called before each test case.
        """
        self.jsonrpc_handler = JSONRPC_Handler(mock.MagicMock())
        self.jsonrpc_handler.handler.__name__ = 'mock_handler'
        self.route_dict = {}
        self.environ = {
            'REQUEST_METHOD': 'GET',
            'commissaire.bus': mock.MagicMock(),

            # RoutesMiddleware inserts this.
            'wsgiorg.routing_args': ((), self.route_dict),
            'routes.route': mock.MagicMock()
        }
        self.start_response = mock.MagicMock()
        self.json_result = {
            'jsonrpc': '2.0',
            'id': '123456789',
            'result': {}
        }
        self.json_error = {
            'jsonrpc': '2.0',
            'id': '123456789',
            'error': {
                'code': 0,
                'message': 'Error message'
            }
        }

    def test_bad_params(self):
        """
        Verify bad parameters trigger a 400 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = None
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('400 Bad Request', mock.ANY)

    def test_error_bad_request(self):
        """
        Verify 'BAD_REQUEST' error code triggers a 400 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.json_error['error']['code'] = C.JSONRPC_ERRORS['BAD_REQUEST']
            self.jsonrpc_handler.handler.return_value = self.json_error
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('400 Bad Request', mock.ANY)

    def test_error_not_found(self):
        """
        Verify 'NOT_FOUND' error code triggers a 404 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.json_error['error']['code'] = C.JSONRPC_ERRORS['NOT_FOUND']
            self.jsonrpc_handler.handler.return_value = self.json_error
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('404 Not Found', mock.ANY)

    def test_error_conflict(self):
        """
        Verify 'CONFLICT' error code triggers a 409 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.json_error['error']['code'] = C.JSONRPC_ERRORS['CONFLICT']
            self.jsonrpc_handler.handler.return_value = self.json_error
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('409 Conflict', mock.ANY)

    def test_error_other(self):
        """
        Verify other error codes raise an Exception.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.json_error['error']['code'] = C.JSONRPC_ERRORS['INTERNAL_ERROR']
            self.jsonrpc_handler.handler.return_value = self.json_error
            self.assertRaises(
                Exception, self.jsonrpc_handler,
                self.environ, self.start_response)

    def test_delete_ok(self):
        """
        Verify a successful DELETE request triggers a 200 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.environ['REQUEST_METHOD'] = 'DELETE'
            self.jsonrpc_handler.handler.return_value = self.json_result
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_get_ok(self):
        """
        Verify a successful GET request triggers a 200 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.environ['REQUEST_METHOD'] = 'GET'
            self.jsonrpc_handler.handler.return_value = self.json_result
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_post_ok(self):
        """
        Verify a successful POST request triggers a 200 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.environ['REQUEST_METHOD'] = 'POST'
            self.jsonrpc_handler.handler.return_value = self.json_result
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_put_ok(self):
        """
        Verify a successful PUT request triggers a 201 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.environ['REQUEST_METHOD'] = 'PUT'
            self.jsonrpc_handler.handler.return_value = self.json_result
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('201 Created', mock.ANY)

    def test_put_with_add_ok(self):
        """
        Verify a successful PUT request with an "add" action triggers a 200 status.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.environ['REQUEST_METHOD'] = 'PUT'
            self.route_dict['action'] = 'add'
            self.jsonrpc_handler.handler.return_value = self.json_result
            body = self.jsonrpc_handler(self.environ, self.start_response)
            self.start_response.assert_called_once_with('200 OK', mock.ANY)

    def test_malformed_jsonrpc_response(self):
        """
        Verify a malformed JSON-RPC response message raises an exception.
        """
        with mock.patch('commissaire_http.handlers.get_params') as get_params:
            get_params.return_value = {}
            self.jsonrpc_handler.handler.return_value = {}
            self.assertRaises(
                Exception, self.jsonrpc_handler,
                self.environ, self.start_response)
