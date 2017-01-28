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

from commissaire_http.dispatcher import Dispatcher
from commissaire_http.router import Router

from commissaire_http.handlers import (
    clusters, hosts, networks, container_managers)
from commissaire_http.handlers.clusters import operations

#: Global HTTP router for the dispatcher
ROUTER = Router(optional_slash=True)
hosts._register(ROUTER)
clusters._register(ROUTER)
networks._register(ROUTER)
operations._register(ROUTER)
container_managers._register(ROUTER)

#: Global HTTP dispatcher for the server
DISPATCHER = Dispatcher(
    ROUTER,
    handler_packages=[
        'commissaire_http.handlers',
        'commissaire_http.handlers.clusters',
        'commissaire_http.handlers.container_managers',
        'commissaire_http.handlers.clusters.operations',
        'commissaire_http.handlers.networks',
        'commissaire_http.handlers.hosts'])
