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

from datetime import datetime as _dt

from commissaire import bus as _bus
from commissaire import models
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire_http.handlers import (
    LOGGER, JSONRPC_Handler, create_jsonrpc_response, create_jsonrpc_error)


def _register(router):
    """
    Sets up routing for hosts.

    :param router: Router instance to attach to.
    :type router: commissaire_http.router.Router
    :returns: The router.
    :rtype: commissaire_http.router.Router
    """
    from commissaire_http.constants import ROUTING_RX_PARAMS

    router.connect(
        R'/api/v0/hosts/',
        controller=list_hosts,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/host/{address}/',
        requirements={'address': ROUTING_RX_PARAMS['address']},
        controller=get_host,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/host/{address}/',
        requirements={'address': ROUTING_RX_PARAMS['address']},
        controller=create_host,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/host/',
        controller=create_host,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/host/{address}/creds',
        requirements={'address': ROUTING_RX_PARAMS['address']},
        controller=get_hostcreds,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/host/{address}/',
        requirements={'address': ROUTING_RX_PARAMS['address']},
        controller=delete_host,
        conditions={'method': 'DELETE'})
    router.connect(
        R'/api/v0/host/{address}/status/',
        controller=get_host_status,
        conditions={'method': 'GET'})

    return router


@JSONRPC_Handler
def list_hosts(message, bus):
    """
    Lists all hosts.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    container = bus.storage.list(models.Hosts)
    return create_jsonrpc_response(
        message['id'],
        [host.to_dict_safe() for host in container.hosts])


@JSONRPC_Handler
def get_host(message, bus):
    """
    Gets a specific host.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        address = message['params']['address']
        host = bus.storage.get_host(address)
        return create_jsonrpc_response(message['id'], host.to_dict_safe())
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Client requested a non-existant host: "{}"'.format(
            message['params']['address']))
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])


@JSONRPC_Handler
def create_host(message, bus):
    """
    Creates a new host.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    LOGGER.debug('create_host params: "{}"'.format(message['params']))
    try:
        address = message['params']['address']
    except KeyError:
        return create_jsonrpc_error(
            message, '"address" must be given in the url or in the PUT body',
            JSONRPC_ERRORS['INVALID_PARAMETERS'])

    # If a cluster if provided, grab it from storage
    cluster_data = {}
    cluster_name = message['params'].get('cluster')
    if cluster_name:
        cluster = _does_cluster_exist(bus, cluster_name)
        if not cluster:
            return create_jsonrpc_error(
                message, 'Cluster does not exist',
                JSONRPC_ERRORS['INVALID_PARAMETERS'])
        else:
            cluster_data = cluster.to_dict()
            LOGGER.debug('Found cluster. Data: "{}"'.format(cluster))
    try:
        host = bus.storage.get_host(address)
        LOGGER.debug('Host "{}" already exisits.'.format(address))

        # Verify the keys match
        if host.ssh_priv_key != message['params'].get('ssh_priv_key', ''):
            return create_jsonrpc_error(
                message, 'Host already exists', JSONRPC_ERRORS['CONFLICT'])

        # Verify the host is in the cluster if it is expected
        if cluster_name and address not in cluster.hostset:
            LOGGER.debug('Host "{}" is not in cluster "{}"'.format(
                address, cluster_name))
            return create_jsonrpc_error(
                message, 'Host not in cluster', JSONRPC_ERRORS['CONFLICT'])

        # Return out now. No more processing needed.
        return create_jsonrpc_response(message['id'], host.to_dict_safe())

    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Brand new host "{}" being created.'.format(
            message['params']['address']))

    # Save the host to the cluster if it isn't already there
    if cluster_name:
        if address not in cluster.hostset:
            cluster.hostset.append(address)
            bus.storage.save(cluster)
            LOGGER.debug('Saved host "{}" to cluster "{}"'.format(
                address, cluster_name))

    try:
        host = bus.storage.save(models.Host.new(**message['params']))

        # pass this off to the investigator
        bus.notify(
            'jobs.investigate',
            params={'address': address, 'cluster_data': cluster_data})

        # Push the host to the Watcher queue
        watcher_record = models.WatcherRecord(
            address=address,
            last_check=_dt.utcnow().isoformat())
        bus.producer.publish(watcher_record.to_json(), 'jobs.watcher')

        return create_jsonrpc_response(message['id'], host.to_dict_safe())
    except models.ValidationError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


@JSONRPC_Handler
def delete_host(message, bus):
    """
    Deletes an existing host.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        address = message['params']['address']
        LOGGER.debug('Attempting to delete host "{}"'.format(address))
        bus.storage.delete(models.Host.new(address=address))
        # TODO: kick off service job to remove the host?

        try:
            # Remove from a cluster
            container = bus.storage.list(models.Clusters)
            for cluster in container.clusters:
                if address in cluster.hostset:
                    LOGGER.info('Removing host "{}" from cluster "{}"'.format(
                        address, cluster.name))
                    cluster.hostset.pop(
                        cluster.hostset.index(address))
                    bus.storage.save(cluster)
                    # A host can only be part of one cluster so break the loop
                    break
        except _bus.RemoteProcedureCallError as error:
            LOGGER.info('{} not part of a cluster.'.format(address))

        return create_jsonrpc_response(message['id'], [])
    except _bus.RemoteProcedureCallError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug('Error deleting host: {}: {}'.format(
            type(error), error))
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


@JSONRPC_Handler
def get_hostcreds(message, bus):
    """
    Gets credentials for a host.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        address = message['params']['address']
        host = bus.storage.get_host(address)
        creds = {
            'remote_user': host.remote_user,
            'ssh_priv_key': host.ssh_priv_key
        }
        return create_jsonrpc_response(message['id'], creds)
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Client requested a non-existant host: "{}"'.format(
            address))
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])


@JSONRPC_Handler
def get_host_status(message, bus):
    """
    Gets the status of an exisiting host.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        address = message['params']['address']
        host = bus.storage.get_host(address)
        status = models.HostStatus.new(
            host={
                'last_check': host.last_check,
                'status': host.status,
            },
            # TODO: Update when we add other types.
            type='host_only')

        LOGGER.debug('Status for host "{0}": "{1}"'.format(
            host.address, status.to_json_safe()))

        return create_jsonrpc_response(message['id'], status.to_dict_safe())
    except _bus.RemoteProcedureCallError as error:
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug(
            'Host Status exception caught for {0}: {1}:{2}'.format(
                address, type(error), error))
        return create_jsonrpc_error(
            message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


def _does_cluster_exist(bus, cluster_name):
    """
    Shorthand to check and see if a cluster exists. If it does, return the
    message response data.

    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :param cluster_name: The name of the Cluster to look up.
    :type cluster_name: str
    :returns: The found Cluster instance or None
    :rtype: mixed
    """
    LOGGER.debug('Checking on cluster "{}"'.format(cluster_name))
    try:
        cluster = bus.storage.get_cluster(cluster_name)
        LOGGER.debug('Found cluster: "{}"'.format(cluster))
        return cluster
    except _bus.StorageLookupError as error:
        LOGGER.warn(
            'create_host could not find cluster "{}"'.format(cluster_name))
        return None
