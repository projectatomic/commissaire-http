#!/usr/bin/env python3
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
Prototype http server.
"""

import logging

from commissaire_http.dispatcher import Dispatcher
from commissaire_http.router import Router
from commissaire_http import CommissaireHttpServer

# NOTE: Only added for this example
for name in ('Dispatcher', 'Router', 'Bus', 'CommissaireHttpServer'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(name)s(%(levelname)s): %(message)s'))
    logger.handlers.append(handler)
# --


# Make a router that takes in "handler"s.
mapper = Router()
mapper.connect(
    R'/hello/',
    controller='commissaire_http.handlers.hello_world',
    conditions={'method': 'GET'})
mapper.connect(
    R'/world/',
    controller='commissaire_http.handlers.create_world',
    conditions={'method': 'PUT'})
mapper.connect(
    R'/hello_class/',
    controller='commissaire_http.handlers.ClassHandlerExample.hello',
    conditions={'method': 'GET'})
mapper.connect(
    R'/api/v0/clusters/',
    controller='commissaire_http.handlers.clusters.list_clusters',
    conditions={'method': 'GET'})

dispatcher = Dispatcher(
    mapper,
    handler_packages=[
        'commissaire_http.handlers',
        'commissaire_http.handlers.clusters'])

try:
    server = CommissaireHttpServer('127.0.0.1', 8000, dispatcher)
    server.setup_bus(
        'commissaire',
        'redis://127.0.0.1:6379/',
        [{'name': 'simple', 'routing_key': 'simple.*'}])
    server.serve_forever()
except KeyboardInterrupt:
    pass
