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
from commissaire import constants as C
from commissaire import models
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire_http.handlers import LOGGER, create_response, return_error


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
    hosts_msg = bus.request('storage.list', params=['Hosts'])
    return create_response(message['id'], hosts_msg['result'])


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
        host_response = bus.request(
            'storage.get', params=[
                'Host', {'address': message['params']['address']}])
        return create_response(message['id'], host_response['result'])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Client requested a non-existant host: "{}"'.format(
            message['params']['address']))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])


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
        return return_error(
            message, '"address" must be given in the url or in the PUT body',
            JSONRPC_ERRORS['INVALID_PARAMETERS'])
    try:
        host = bus.request('storage.get', params=[
            'Host', {'address': address}, True])
        LOGGER.debug('Host "{}" already exisits.'.format(address))

        # Verify the keys match
        if (host['result']['ssh_priv_key'] !=
                message['params'].get('ssh_priv_key', '')):
            return return_error(
                message, 'Host already exists', JSONRPC_ERRORS['CONFLICT'])

        # Verify the cluster exists and it's in the cluster
        if message['params'].get('cluster'):
            cluster = _does_cluster_exist(bus, message['params']['cluster'])
            if not cluster:
                return return_error(
                    message, 'Cluster does not exist',
                    JSONRPC_ERRORS['INVALID_PARAMETERS'])
            # Verify the host is in the cluster
            if address not in cluster.hostset:
                LOGGER.debug('Host "{}" is not in cluster "{}"'.format(
                    address, message['params']['cluster']))
                return return_error(
                    message, 'Host not in cluster', JSONRPC_ERRORS['CONFLICT'])

        # Return out now. No more processing needed.
        return create_response(
            message['id'], models.Host.new(**host['result']).to_dict())

    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Brand new host "{}" being created.'.format(
            message['params']['address']))

    if message['params'].get('cluster'):
        # Verify the cluster existence and add the host to it
        cluster_name = message['params']['cluster']
        cluster = _does_cluster_exist(bus, message['params']['cluster'])
        if not cluster:
            LOGGER.warn(
                'create_host could not find cluster "{}" for the creation '
                'of new host "{}"'.format(cluster_name, address))
            return return_error(
                message,
                'Cluster does not exist',
                JSONRPC_ERRORS['INVALID_PARAMETERS'])

        LOGGER.debug('Found cluster. Data: "{}"'.format(cluster))
        if address not in cluster.hostset:
            cluster.hostset.append(address)
            bus.request('storage.save', params=[
                'Cluster', cluster.to_dict(True)])

    try:
        host = models.Host.new(**message['params'])
        host._validate()
        bus.request(
            'storage.save', params=[
                'Host', host.to_dict(True)])

        # pass this off to the investigator
        bus.notify('jobs.investigate', params={'address': address})

        # Push the host to the Watcher queue
        watcher_record = models.WatcherRecord(
            address=address,
            last_check=_dt.utcnow().isoformat())
        bus.producer.publish(watcher_record.to_json(), 'jobs.watcher')

        return create_response(message['id'], host.to_dict())
    except models.ValidationError as error:
        return return_error(message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


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
        bus.request('storage.delete', params=[
            'Host', {'address': address}])
        # TODO: kick off service job to remove the host?

        # Remove from a cluster
        for cluster in bus.request(
                'storage.list', params=['Clusters', True])['result']:
            if address in cluster['hostset']:
                LOGGER.info('Removing host "{}" from cluster "{}"'.format(
                    address, cluster['name']))
                cluster['hostset'].pop(
                    cluster['hostset'].index(address))
                bus.request('storage.save', params=['Cluster', cluster])
                # A host can only be part of one cluster so break the loop
                break
        return create_response(message['id'], [])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Error deleting host: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug('Error deleting host: {}: {}'.format(
            type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['INTERNAL_ERROR'])


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
        host_response = bus.request(
            'storage.get', params=[
                'Host', {'address': message['params']['address']}, True])
        creds = {
            'remote_user': host_response['result']['remote_user'],
            'ssh_priv_key': host_response['result']['ssh_priv_key']
        }
        return create_response(message['id'], creds)
    except _bus.RemoteProcedureCallError as error:
        LOGGER.debug('Client requested a non-existant host: "{}"'.format(
            message['params']['address']))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])


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
        host_response = bus.request('storage.get', params=[
            'Host', {'address': message['params']['address']}])
        host = models.Host.new(**host_response['result'])
        status = models.HostStatus.new(
            host={
                'last_check': host.last_check,
                'status': host.status,
            },
            # TODO: Update when we add other types.
            type=C.CLUSTER_TYPE_HOST)

        LOGGER.debug('Status for host "{0}": "{1}"'.format(
            host.address, status.to_json()))

        return create_response(message['id'], status.to_dict())
    except _bus.RemoteProcedureCallError as error:
        LOGGER.warn('Could not retrieve host "{}". {}: {}'.format(
            message['params']['address'], type(error), error))
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        LOGGER.debug(
            'Host Status exception caught for {0}: {1}:{2}'.format(
                host.address, type(error), error))
        return return_error(
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
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': cluster_name}, True])
        LOGGER.debug('Found cluster: "{}"'.format(cluster))
        return models.Cluster.new(**cluster['result'])
    except _bus.RemoteProcedureCallError as error:
        LOGGER.warn(
            'create_host could not find cluster "{}"'.format(cluster_name))
        LOGGER.debug('Error: {}: "{}"'.format(type(error), error))
