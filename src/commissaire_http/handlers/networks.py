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
Networks handlers.
"""

from commissaire import models
from commissaire import bus as _bus
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire_http.handlers import create_response, return_error


def list_networks(message, bus):
    """
    Lists all networks.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    networks_msg = bus.request('storage.list', params=['Networks'])
    return create_response(
        message['id'],
        [network['name'] for network in networks_msg['result']])


def get_network(message, bus):
    """
    Gets a specific network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        network_response = bus.request(
            'storage.get', params=[
                'Network', {'name': message['params']['name']}, True])
        network = models.Network.new(**network_response['result'])

        return create_response(message['id'], network.to_dict())
    except _bus.RemoteProcedureCallError as error:
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])
