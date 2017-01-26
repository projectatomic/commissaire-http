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
                    'Unable to read "wsgi.input": {}'.format(error))
                return None
    else:
        param_dict.update(parse_query_string(environ.get('QUERY_STRING')))

    return param_dict


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
    LOGGER.error('Error dealing with: "{}"'.format(message))
    response = create_jsonrpc_response(
        message['id'], error=error,
        error_code=error_code)
    LOGGER.debug('Returning: {}'.format(response))
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
