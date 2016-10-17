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
Routing items.
"""

from commissaire_http.constants import ROUTING_RX_PARAMS

from commissaire_http.dispatcher import Dispatcher
from commissaire_http.router import Router

#: Global HTTP router for the dispatcher
ROUTER = Router(optional_slash=True)
ROUTER.connect(
    R'/api/v0/clusters/',
    controller='commissaire_http.handlers.clusters.list_clusters',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.clusters.get_cluster',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.clusters.create_cluster',
    conditions={'method': 'PUT'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/hosts/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.clusters.list_cluster_members',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/hosts/{host}/',
    requirements={
        'name': ROUTING_RX_PARAMS['name'],
        'host': ROUTING_RX_PARAMS['host'],
    },
    controller='commissaire_http.handlers.clusters.check_cluster_member',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/hosts/{host}/',
    requirements={
        'name': ROUTING_RX_PARAMS['name'],
        'host': ROUTING_RX_PARAMS['host'],
    },
    controller='commissaire_http.handlers.clusters.add_cluster_member',
    conditions={'method': 'PUT'})
ROUTER.connect(
    R'/api/v0/cluster/{name}/hosts/{host}/',
    requirements={
        'name': ROUTING_RX_PARAMS['name'],
        'host': ROUTING_RX_PARAMS['host'],
    },
    controller='commissaire_http.handlers.clusters.delete_cluster_member',
    conditions={'method': 'DELETE'})
# Networks
ROUTER.connect(
    R'/api/v0/networks/',
    controller='commissaire_http.handlers.networks.list_networks',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/network/{name}/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.networks.get_network',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/network/{name}/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.networks.create_network',
    conditions={'method': 'PUT'})
ROUTER.connect(
    R'/api/v0/network/{name}/',
    requirements={'name': ROUTING_RX_PARAMS['name']},
    controller='commissaire_http.handlers.networks.delete_network',
    conditions={'method': 'DELETE'})
# Hosts
ROUTER.connect(
    R'/api/v0/hosts/',
    controller='commissaire_http.handlers.hosts.list_hosts',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/host/{address}/',
    requirements={'address': ROUTING_RX_PARAMS['address']},
    controller='commissaire_http.handlers.hosts.get_host',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/host/{address}/',
    requirements={'address': ROUTING_RX_PARAMS['address']},
    controller='commissaire_http.handlers.hosts.create_host',
    conditions={'method': 'PUT'})
ROUTER.connect(
    R'/api/v0/host/',
    controller='commissaire_http.handlers.hosts.create_host',
    conditions={'method': 'PUT'})
ROUTER.connect(
    R'/api/v0/host/{address}/creds',
    requirements={'address': ROUTING_RX_PARAMS['address']},
    controller='commissaire_http.handlers.hosts.get_hostcreds',
    conditions={'method': 'GET'})
ROUTER.connect(
    R'/api/v0/host/{address}/',
    requirements={'address': ROUTING_RX_PARAMS['address']},
    controller='commissaire_http.handlers.hosts.delete_host',
    conditions={'method': 'DELETE'})
ROUTER.connect(
    R'/api/v0/host/{address}/status/',
    controller='commissaire_http.handlers.hosts.get_host_status',
    conditions={'method': 'GET'})

#: Global HTTP dispatcher for the server
DISPATCHER = Dispatcher(
    ROUTER,
    handler_packages=[
        'commissaire_http.handlers',
        'commissaire_http.handlers.clusters',
        'commissaire_http.handlers.networks',
        'commissaire_http.handlers.hosts'])
