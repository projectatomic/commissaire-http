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
Built-in handlers.
"""

import json
import logging
import uuid

from html import escape
from urllib.parse import parse_qs

from commissaire_http.constants import JSONRPC_ERRORS

#: Handler specific logger
LOGGER = logging.getLogger('Handlers')


def parse_query_string(qs):
    """
    Parses a query string into parameters.

    :param qs: A query string.
    :type qs: str
    :returns: A dictionary of parameters.
    :rtype: dict
    """
    new_qs = {}
    for key, value in parse_qs(qs).items():
        if len(value) == 1:
            new_qs[key] = escape(value[0])
        else:
            new_value = []
            for item in value:
                new_value.append(escape(item))
            new_qs[key] = new_value
    return new_qs


def get_params(environ):
    """
    Handles pulling parameters out of the various inputs.

    :param environ: WSGI environment dictionary.
    :type environ: dict
    :returns: A parameter dictionary.
    :rtype: dict
    """
    route_dict, route = environ['commissaire.routematch']
    param_dict = {}

    # Initial parameters come from the urllib.
    for param_key in route.minkeys:
        param_dict[param_key] = route_dict[param_key]

    # If we are a PUT or POST, look for parameters in wsgi.input.
    if environ['REQUEST_METHOD'] in ('PUT', 'POST'):
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
        except ValueError:
            content_length = 0
        if content_length > 0:
            try:
                wsgi_input = environ['wsgi.input'].read(content_length)
                more_params = json.loads(wsgi_input.decode())
                param_dict.update(more_params)
            except (ValueError, json.decoder.JSONDecodeError) as error:
                LOGGER.error(
                    'Unable to read "wsgi.input": %s', error)
                return None
    else:
        param_dict.update(parse_query_string(environ.get('QUERY_STRING')))

    return param_dict


class BasicHandler(object):
    """
    Base decorator class for handler functions.

    Calls the handler function without any extra processing.

    All other handler classes should be derived from the BasicHandler class.
    The BasicHandler class itself serves only as a tag when loading handlers.
    """

    def __init__(self, handler):
        """
        Stashes the handler function to be used in __call__().

        :param handler: Handler function.
        :type handler: callable
        """
        self.handler = handler

    def __call__(self, environ, start_response):
        """
        Calls the handler function without any extra processing.

        :param environ: WSGI environment dictionary.
        :type environ: dict
        :param start_response: WSGI start_response callable.
        :type start_response: callable
        """
        return self.handler(environ, start_response)


class JSONRPC_Handler(BasicHandler):
    """
    Decorator class for JSON-RPC handler functions.

    Converts HTTP parameters to a JSON-RPC message, and converts errors in a
    JSON-RPC response to HTTP error codes.
    """

    def __call__(self, environ, start_response):
        """
        Calls the JSON-RPC handler function, with extra processing before and
        after.

        :param environ: WSGI environment dictionary.
        :type environ: dict
        :param start_response: WSGI start_response callable.
        :type start_response: callable
        """

        bus = environ['commissaire.bus']
        route_dict, route = environ['commissaire.routematch']

        # Extract request parameters.
        param_dict = get_params(environ)
        if param_dict is None:
            start_response(
                '400 Bad Request', [('content-type', 'text/html')])
            return [bytes('Bad Request', 'utf8')]

        # 'method' is normally supposed to be the method to be
        # called, but we hijack it for the HTTP request method.
        jsonrpc_message = {
            'jsonrpc': '2.0',
            'id': str(uuid.uuid4()),
            'method': environ['REQUEST_METHOD'],
            'params': param_dict
        }
        LOGGER.debug(
            'Request transformed to "%s"', jsonrpc_message)

        result = self.handler(jsonrpc_message, bus)

        handler_name = self.handler.__name__
        LOGGER.debug('Handler %s returned "%s"', handler_name, result)

        if 'error' in result.keys():
            error_code = result['error']['code']
            if error_code == JSONRPC_ERRORS['BAD_REQUEST']:
                status = '400 Bad Request'
            elif error_code == JSONRPC_ERRORS['NOT_FOUND']:
                status = '404 Not Found'
            elif error_code == JSONRPC_ERRORS['METHOD_NOT_ALLOWED']:
                status = '405 Method Not Allowed'
            elif error_code == JSONRPC_ERRORS['CONFLICT']:
                status = '409 Conflict'
            else:
                message = 'Unhandled error code {}'.format(error_code)
                LOGGER.error('%s: %s', message, result)
                raise Exception(message)
            start_response(status, [('content-type', 'text/html')])
            response_body = status[4:]

        elif 'result' in result.keys():
            status = '200 OK'
            if environ['REQUEST_METHOD'] == 'PUT':
                # action=add is for endpoints that add a
                # member to a set, in which case nothing
                # is being created, so return 200 OK.
                if route_dict.get('action') != 'add':
                    status = '201 Created'
            start_response(status, [('content-type', 'application/json')])
            response_body = json.dumps(result['result'])

        else:
            message = 'Malformed JSON-RPC response message'
            self.logger.error('%s: %s', message, result)
            raise Exception(message)

        return [bytes(response_body, 'utf8')]


def create_jsonrpc_error(message, error, error_code):
    """
    Shortcut for logging and returning an error.

    :param message: jsonrpc message structure.
    :type message: dict
    :param error: The error to send back to the requestor.
    :type error: str or Exception
    :param error_code: JSONRPC error code.
    :type error_code: int
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    LOGGER.error('Error dealing with: "%s"', message)
    response = create_jsonrpc_response(
        message['id'], error=error,
        error_code=error_code)
    LOGGER.debug('Returning: %s', response)
    return response


def create_jsonrpc_response(id, result=None, error=None,
                            error_code=JSONRPC_ERRORS['INTERNAL_ERROR']):
    """
    Creates a jsonrpc response based on input.

    :param id: The unique id that came from the request.
    :type id: str
    :param result: The result to send back to the requestor.
    :type result: mixed
    :param error: The error to send back to the requestor.
    :type error: str or Exception
    :param error_code: JSONRPC error code. Defaults to Internal Error.
    :type error_code: int
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    jsonrpc_response = {
        'jsonrpc': '2.0',
        'id': id,
    }
    if result is not None:
        jsonrpc_response['result'] = result
    elif error:
        jsonrpc_response['error'] = {
            'code': error_code,
            'message': str(error),
        }
        if isinstance(error, Exception):
            jsonrpc_response['error']['data'] = {
                'exception': str(type(error))}
    else:
        raise TypeError('Either a result or error is required.')
    return jsonrpc_response


@JSONRPC_Handler
def hello_world(message, bus):  # pragma: no cover
    """
    Example function handler that simply says hello. If name is given
    in the query string it uses it.

    :param message: jsonrpc message structure.
    :type message: dict
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    response_msg = {'Hello': 'there'}
    # Example of using the bus ...
    # print(bus.request('simple.add', 'add', params=[10, 20]))
    if message['params'].get('name'):
        response_msg['Hello'] = message['params']['name']
    return create_jsonrpc_response(message['id'], response_msg)


@JSONRPC_Handler
def create_world(message, bus):  # pragma: no cover
    """
    Example function handler that simply says hello. If name is given
    in the query string it uses it.

    :param message: jsonrpc message structure.
    :type message: dict
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        import random
        return create_jsonrpc_response(
            message['id'],
            {
                'name': message['params'].get('name'),
                'radius': random.randint(2000, 8000),
                'age_in_billions': random.randint(2, 9)
            })
    except Exception as error:
        raise error


class ClassHandlerExample:  # pragma: no cover
    """
    Example class based handlers.
    """

    @JSONRPC_Handler
    def hello(self, message, bus):
        """
        Example method handler that simply says hello. If name is given
        in the query string it uses it.

        :param message: jsonrpc message structure.
        :type message: dict
        :returns: A jsonrpc structure.
        :rtype: dict
        """
        return hello_world(message, bus)
