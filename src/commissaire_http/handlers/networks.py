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
from commissaire_http.handlers import LOGGER, create_response, return_error


def _register(router):
    """
    Sets up routing for clusters.

    :param router: Router instance to attach to.
    :type router: commissaire_http.router.Router
    :returns: The router.
    :rtype: commissaire_http.router.Router
    """
    from commissaire_http.constants import ROUTING_RX_PARAMS

    # Networks
    router.connect(
        R'/api/v0/networks/',
        controller=list_networks,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=get_network,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=create_network,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/network/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=delete_network,
        conditions={'method': 'DELETE'})

    return router


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

        return create_response(message['id'], network.to_dict_safe())
    except _bus.RemoteProcedureCallError as error:
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])


def create_network(message, bus):
    """
    Creates a new network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        LOGGER.debug('create_network params: {}'.format(message['params']))
        # Check to see if we already have a network with that name
        network = bus.request('storage.get', params=[
            'Network', {'name': message['params']['name']}])
        LOGGER.debug(
            'Creation of already exisiting network "{0}" requested.'.format(
                message['params']['name']))

        # If they are the same thing then go ahead and return success
        if models.Network.new(
            **network['result']).to_dict() == models.Network.new(
                **message['params']).to_dict():
            return create_response(message['id'], network['result'])

        # Otherwise error with a CONFLICT
        return return_error(
            message,
            'A network with that name already exists.',
            JSONRPC_ERRORS['CONFLICT'])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Error getting network: {}: {}'.format(
            type(error), error))
        LOGGER.info('Attempting to create new network: "{}"'.format(
            message['params']))

    # Create the new network
    try:
        network = models.Network.new(**message['params'])
        network._validate()
        response = bus.request(
            'storage.save', params=[
                'Network', network.to_dict()])
        return create_response(message['id'], response['result'])
    except models.ValidationError as error:
        return return_error(message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


def delete_network(message, bus):
    """
    Deletes an exisiting network.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        LOGGER.debug('Attempting to delete network "{}"'.format(
            message['params']['name']))
        bus.request('storage.delete', params=[
            'Network', {'name': message['params']['name']}])
        return create_response(message['id'], [])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Error deleting network: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug('Error deleting network: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])
