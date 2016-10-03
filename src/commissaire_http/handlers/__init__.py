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

import logging

#: Handler specific logger
LOGGER = logging.getLogger('Handlers')


def create_response(id, result=None, error=None):
    """
    Creates a jsonrpc response based on input.

    :param id: The unique id that came from the request.
    :type id: str
    :param result: The result to send back to the requestor.
    :type result: mixed
    :param error: The error to send back to the requestor.
    :type error: dict
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    jsonrpc_response = {
        'jsonrpc': '2.0',
        'id': id,
    }
    if result:
        jsonrpc_response['result'] = result
    elif error:
        jsonrpc_response['error'] = {
            'code': -32603,  # Default to Internal Error
            'message': error,
        }
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
    return create_response(message['id'], response_msg)


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
        return create_response(
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
