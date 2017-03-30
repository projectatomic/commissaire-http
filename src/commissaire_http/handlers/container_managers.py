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
from commissaire_http.handlers import (
    LOGGER, JSONRPC_Handler, create_jsonrpc_response, create_jsonrpc_error)


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
        R'/api/v0/containermanagers/',
        controller=list_container_managers,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/containermanager/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=get_container_manager,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/containermanager/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=create_container_manager,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/containermanager/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=delete_container_manager,
        conditions={'method': 'DELETE'})

    return router


@JSONRPC_Handler
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
    container = bus.storage.list(models.ContainerManagerConfigs)
    return create_jsonrpc_response(
        message['id'], [cmc.name for cmc in container.container_managers])


@JSONRPC_Handler
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
        name = message['params']['name']
        container_manager_cfg = bus.storage.get(
            models.ContainerManagerConfig.new(name=name))

        return create_jsonrpc_response(
            message['id'], container_manager_cfg.to_dict_safe())
    except _bus.StorageLookupError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


@JSONRPC_Handler
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
        name = message['params']['name']
        LOGGER.debug('create_container_manager params: %s', message['params'])
        # Check to see if we already have a network with that name
        input_cmc = models.ContainerManagerConfig.new(**message['params'])
        saved_cmc = bus.storage.get(input_cmc)
        LOGGER.debug(
            'Creation of already exisiting '
            'ContainerManagerConfig "%s" requested.', name)

        # If they are the same thing then go ahead and return success
        if saved_cmc.to_dict() == input_cmc.to_dict():
            return create_jsonrpc_response(
                message['id'], saved_cmc.to_dict_safe())

        # Otherwise error with a CONFLICT
        return create_jsonrpc_error(
            message,
            'A ContainerManager with that name already exists.',
            JSONRPC_ERRORS['CONFLICT'])
    except _bus.StorageLookupError as error:
        LOGGER.info(
            'Attempting to create new ContainerManagerConfig: "%s"',
            message['params'])

    # Create the new ContainerManagerConfig
    try:
        input_cmc = models.ContainerManagerConfig.new(**message['params'])
        saved_cmc = bus.storage.save(input_cmc)
        return create_jsonrpc_response(message['id'], saved_cmc.to_dict_safe())
    except models.ValidationError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


@JSONRPC_Handler
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
        name = message['params']['name']
        LOGGER.debug('Attempting to delete ContainerManagerConfig "%s"', name)
        bus.storage.delete(models.ContainerManagerConfig.new(name=name))
        return create_jsonrpc_response(message['id'], [])
    except _bus.StorageLookupError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug(
            'Error deleting ContainerManagerConfig: %s: %s',
            type(error), error)
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])
