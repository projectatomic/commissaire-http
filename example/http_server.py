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

from commissaire_http.dispatcher import Dispatcher
from commissaire_http.router import Router
from commissaire_http import CommissaireHttpServer

# Make a router that takes in "handler"s.
mapper = Router()
mapper.connect(
    R'/api/v0/{handler:[a-z]*}/',
    topic='http.{handler}.list',
    conditions={'method': 'GET'})

dispatcher = Dispatcher(
    mapper,
    'commissaire',
    'redis://127.0.0.1:6379/'
)

try:
    server = CommissaireHttpServer('127.0.0.1', 8000, dispatcher)
    server.serve_forever()
except KeyboardInterrupt:
    pass
