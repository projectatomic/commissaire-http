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


from wsgiref.simple_server import WSGIServer, make_server
from socketserver import ThreadingMixIn

from kombu import Exchange

# See https://gist.github.com/ashcrow/ecb611337dba966c4255697e6c0a204d
from commissaire_http.dispatcher import Dispatcher
from commissaire_http.topicrouter import TopicRouter
# ---

# Make a topic router that takes in "handler"s.
mapper = TopicRouter()
mapper.register(
    '^/api/v0/(?P<handler>[a-z]*)/?$',
    'http.{handler}')

# Create the dispatcher
dispatcher = Dispatcher(mapper, Exchange('commissaire', type='direct'))


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """
    Threaded version of the WSIServer
    """
    pass


try:
    httpd = make_server(
        '127.0.0.1',
        8000,
        dispatcher.dispatch, server_class=ThreadedWSGIServer)
    print('---\nMake sure redis and clusterservice is running and'
          ' head to http://127.0.0.1:8000/api/v0/clusters/\n---')
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
