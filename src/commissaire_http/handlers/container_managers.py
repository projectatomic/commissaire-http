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
ContainerManagerConfig handlers.
"""

from commissaire import models
from commissaire import bus as _bus
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire_http.handlers import LOGGER, create_response, return_error


def _register(router):  # pragma: no cover
    """
    Sets up routing for ContainerManagerConfigs.

    :param router: Router instance to attach to.
    :type router: commissaire_http.router.Router
    :returns: The router.
    :rtype: commissaire_http.router.Router
    """
    from commissaire_http.constants import ROUTING_RX_PARAMS

    # Networks
    router.connect(
        R'/api/v0/container_managers/',
        controller=list_container_managers,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/container_managers/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=get_container_manager,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/container_managers/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=create_container_manager,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/container_managers/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=delete_container_manager,
        conditions={'method': 'DELETE'})

    return router


def list_container_managers(message, bus):
    """
    Lists all ContainerManagerConfigs.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    msg = bus.request(
        'storage.list', params=['ContainerManagerConfigs'])
    return create_response(
        message['id'], [cmc['name'] for cmc in msg['result']])


def get_container_manager(message, bus):
    """
    Gets a specific ContainerManagerConfig.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        response = bus.request(
            'storage.get', params=[
                'ContainerManagerConfig',
                {'name': message['params']['name']}, True])
        container_manager_cfg = models.Network.new(**response['result'])

        return create_response(message['id'], container_manager_cfg.to_dict())
    except _bus.RemoteProcedureCallError as error:
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])


def create_container_manager(message, bus):
    """
    Creates a new ContainerManagerConfig.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        LOGGER.debug('create_container_manager params: {}'.format(
            message['params']))
        # Check to see if we already have a network with that name
        cmc = bus.request('storage.get', params=[
            'ContainerManagerConfig', {'name': message['params']['name']}])
        LOGGER.debug(
            'Creation of already exisiting ContainerManagerConfig '
            '"{}" requested.'.format(message['params']['name']))

        # If they are the same thing then go ahead and return success
        if models.ContainerManagerConfig.new(
            **cmc['result']).to_dict() == models.ContainerManagerConfig.new(
                **message['params']).to_dict():
            return create_response(message['id'], cmc['result'])

        # Otherwise error with a CONFLICT
        return return_error(
            message,
            'A ContainerManager with that name already exists.',
            JSONRPC_ERRORS['CONFLICT'])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Error getting ContainerManagerConfig: {}: {}'.format(
            type(error), error))
        LOGGER.info(
            'Attempting to create new ContainerManagerConfig: "{}"'.format(
                message['params']))

    # Create the new ContainerManagerConfig
    try:
        cmc = models.ContainerManagerConfig.new(**message['params'])
        cmc._validate()
        response = bus.request(
            'storage.save', params=[
                'ContainerManagerConfig', cmc.to_dict()])
        return create_response(message['id'], response['result'])
    except models.ValidationError as error:
        return return_error(message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


def delete_container_manager(message, bus):
    """
    Deletes an exisiting ContainerManagerConfig.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        LOGGER.debug('Attempting to delete ContainerManagerConfig "{}"'.format(
            message['params']['name']))
        bus.request('storage.delete', params=[
            'ContainerManagerConfig', {'name': message['params']['name']}])
        return create_response(message['id'], [])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Error deleting ContainerManagerConfig: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug('Error deleting ContainerManagerConfig: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])
