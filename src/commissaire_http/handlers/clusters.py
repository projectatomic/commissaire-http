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
Clusters handlers.
"""

from commissaire import constants as C
from commissaire_http.constants import JSONRPC_ERRORS
from commissaire import models

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

    router.connect(
        R'/api/v0/clusters/',
        controller=list_clusters,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/cluster/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=get_cluster,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/cluster/{name}/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=create_cluster,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/cluster/{name}/hosts/',
        requirements={'name': ROUTING_RX_PARAMS['name']},
        controller=list_cluster_members,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/cluster/{name}/hosts/{host}/',
        requirements={
            'name': ROUTING_RX_PARAMS['name'],
            'host': ROUTING_RX_PARAMS['host'],
        },
        controller=check_cluster_member,
        conditions={'method': 'GET'})
    router.connect(
        R'/api/v0/cluster/{name}/hosts/{host}/',
        requirements={
            'name': ROUTING_RX_PARAMS['name'],
            'host': ROUTING_RX_PARAMS['host'],
        },
        controller=add_cluster_member,
        conditions={'method': 'PUT'})
    router.connect(
        R'/api/v0/cluster/{name}/hosts/{host}/',
        requirements={
            'name': ROUTING_RX_PARAMS['name'],
            'host': ROUTING_RX_PARAMS['host'],
        },
        controller=delete_cluster_member,
        conditions={'method': 'DELETE'})

    return router


def list_clusters(message, bus):
    """
    Lists all clusters.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    clusters_msg = bus.request('storage.list', params=['Clusters'])
    return create_response(
        message['id'],
        [cluster['name'] for cluster in clusters_msg['result']])


def get_cluster(message, bus):
    """
    Gets a specific cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    cluster_response = bus.request(
        'storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])
    cluster = models.Cluster.new(**cluster_response['result'])
    hosts_response = bus.request('storage.list', params=['Hosts'])

    available = unavailable = total = 0

    for host in hosts_response['result']:
        if host['address'] in cluster.hostset:
            total += 1
            if host['status'] == 'active':
                available += 1
            else:
                unavailable += 1

    cluster.hosts['total'] = total
    cluster.hosts['available'] = available
    cluster.hosts['unavailable'] = unavailable

    return create_response(message['id'], cluster.to_dict_with_hosts())


def create_cluster(message, bus):
    """
    Creates a new cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}])
        LOGGER.debug(
            'Creation of already exisiting cluster {0} requested.'.format(
                message['params']['name']))
    except Exception as error:
        LOGGER.debug('Brand new cluster being created.')

        if message['params'].get('network'):
            # Verify the networks existence
            try:
                bus.request('storage.get', params=[
                    'Network', {'name': message['params']['network']}
                ])
            except Exception as error:
                # Default if the network doesn't exist
                message['params']['network'] = C.DEFAULT_CLUSTER_NETWORK_JSON['name']  # noqa

    try:
        cluster = models.Cluster.new(**message['params'])
        cluster._validate()
        response = bus.request(
            'storage.save', params=[
                'Cluster', cluster.to_dict()])
        return create_response(message['id'], response['result'])
    except models.ValidationError as error:
        return return_error(message, error, JSONRPC_ERRORS['INVALID_REQUEST'])


def list_cluster_members(message, bus):
    """
    Lists hosts in a cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    response = None
    try:
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])
        LOGGER.debug('Cluster found: {}'.format(cluster['result']['name']))
        LOGGER.debug('Returning: {}'.format(response))
        return create_response(
            message['id'], result=cluster['result']['hostset'])
    except Exception as error:
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])


def update_cluster_members(message, bus):
    """
    Updates the list of members in a cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        old_hosts = set(message['params']['old'])  # Ensures no duplicates
        new_hosts = set(message['params']['new'])  # Ensures no duplicates
        LOGGER.debug('old_hosts="{}", new_hosts="{}"'.format(
            old_hosts, new_hosts))
    except Exception as error:
        return return_error(message, error, JSONRPC_ERRORS['BAD_REQUEST'])

    try:
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])
    except Exception as error:
        return return_error(message, error, JSONRPC_ERRORS['NOT_FOUND'])

    if old_hosts != set(cluster['result']['hostset']):
        msg = 'Conflict setting hosts for cluster {0}'.format(
            cluster['result']['name'])
        LOGGER.error(msg)
        return return_error(message, msg, JSONRPC_ERRORS['CONFLICT'])

    # FIXME: Need input validation.  For each new host,
    #        - Does the host exist at /commissaire/hosts/{IP}?
    #        - Does the host already belong to another cluster?

    # FIXME: Should guard against races here, since we're fetching
    #        the cluster record and writing it back with some parts
    #        unmodified.  Use either locking or a conditional write
    #        with the etcd 'modifiedIndex'.  Deferring for now.
    cluster['result']['hostset'] = list(new_hosts)
    cluster = models.Cluster.new(**cluster['result'])
    cluster._validate()
    response = bus.request(
        'storage.save', params=[
            'Cluster', cluster.to_dict()])
    return create_response(message['id'], response['result'])


def check_cluster_member(message, bus):
    """
    Checks is a member is part of the cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])
        if message['params']['host'] in cluster['result']['hostset']:
            # Return back the host in a list
            return create_response(message['id'], [message['params']['host']])
        else:
            return create_response(
                message['id'],
                error='The requested host is not part of the cluster.',
                error_code=JSONRPC_ERRORS['NOT_FOUND'])
    except Exception as error:
        return create_response(
            message['id'],
            error=error,
            error_code=JSONRPC_ERRORS['INTERNAL_ERROR'])


def add_cluster_member(message, bus):
    """
    Adds a member to the cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])

        if message['params']['host'] not in cluster['result']['hostset']:
            # FIXME: Need input validation.
            #        - Does the host exist at /commissaire/hosts/{IP}?
            #        - Does the host already belong to another cluster?

            # FIXME: Should guard against races here, since we're fetching
            #        the cluster record and writing it back with some parts
            #        unmodified.  Use either locking or a conditional write
            #        with the etcd 'modifiedIndex'.  Deferring for now.
            cluster['result']['hostset'].append(message['params']['host'])
            bus.request('storage.save', params=[
                'Cluster', cluster['result'], True])

        # Return back the host in a list
        return create_response(message['id'], [message['params']['host']])
    except Exception as error:
        return create_response(
            message['id'],
            error=error,
            error_code=JSONRPC_ERRORS['INTERNAL_ERROR'])


def delete_cluster_member(message, bus):
    """
    Deletes a member from the cluster.

    :param message: jsonrpc message structure.
    :type message: dict
    :param bus: Bus instance.
    :type bus: commissaire_http.bus.Bus
    :returns: A jsonrpc structure.
    :rtype: dict
    """
    try:
        cluster = bus.request('storage.get', params=[
            'Cluster', {'name': message['params']['name']}, True])
        if message['params']['host'] in cluster['result']['hostset']:
            # FIXME: Should guard against races here, since we're fetching
            #        the cluster record and writing it back with some parts
            #        unmodified.  Use either locking or a conditional write
            #        with the etcd 'modifiedIndex'.  Deferring for now.
            idx = cluster['result']['hostset'].index(message['params']['host'])
            cluster['result']['hostset'].pop(idx)
            bus.request('storage.save', params=[
                'Cluster', cluster['result'], True])
        return create_response(
            message['id'],
            [])
    except Exception as error:
        return create_response(
            message['id'],
            error=error,
            error_code=JSONRPC_ERRORS['NOT_FOUND'])
