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


import json

from commissaire_http.authentication import Authenticator
from commissaire_http.authentication import decode_basic_auth


class HTTPBasicAuth(Authenticator):
    """
    Basic auth implementation of an authenticator.
    """

    def __init__(self, app, filepath=None, users={}):
        """
        Creates an instance of the HTTPBasicAuth authenticator.

        If a 'filepath' is specified, the file's content is loaded and, if
        applicable, merged into the 'users' dictionary.  If no arguments are
        given, the instance attempts to retrieve user passwords from etcd.

        :param app: The WSGI application being wrapped with authenticaiton.
        :type app: callable
        :param filepath: Path to a JSON file containing hashed passwords
        :type filepath: str or None
        :param users: A dictionary of user names and hashed passwords, or None
        :type users: dict or None
        :returns: HTTPBasicAuth
        """
        super(HTTPBasicAuth, self).__init__(app)
        self._data = users
        if filepath is not None:
            self._load_from_file(filepath)
        # elif users is None:
        #     self._load_from_etcd()

    '''
    def _load_from_etcd(self):
        """
        Loads authentication information from etcd.
        """
        store_manager = cherrypy.engine.publish('get-store-manager')[0]
        try:
            key = '/commissaire/config/httpbasicauthbyuserlist'
            d = store_manager.get(key)
        except ValueError as error:
            self.logger.warn(
                'User configuration in Etcd is not valid JSON. Raising...')
            self._data = {}
            raise error
        except Exception as error:
            self.logger.warn(
                'User configuration not found in Etcd. Raising...')
            self._data = {}
            raise error

        self._data = json.loads(d.value)
        self.logger.info('Loaded authentication data from Etcd.')
    '''

    def _load_from_file(self, path):
        """
        Loads authentication information from a JSON file.

        :param path: Path to the JSON file
        :type path: str
        """
        try:
            with open(path, 'r') as afile:
                self._data.update(json.load(afile))
                self.logger.info('Loaded authentication data from local file.')
        except (ValueError, IOError) as error:
            self.logger.warn(
                'Denying all access due to problem parsing '
                'JSON file: {0}'.format(error))

    def check_authentication(self, user, passwd):
        """
        Checks the user name and password from an Authorization header
        against the loaded datastore.

        :param user: User nane
        :type user: string
        :param passwd: Password
        :type passwd: string
        :returns: Whether access is granted
        :rtype: bool
        """
        import bcrypt

        valid = False
        hashed = self._data[user]['hash']
        try:
            if bcrypt.hashpw(passwd.encode('utf-8'), hashed) == hashed:
                self.logger.debug(
                    'The provided hash for user {0} '
                    'matched: {1}'.format(user, passwd))

                valid = True
        except ValueError:
            pass  # Bad salt

        return valid

    def authenticate(self, environ, start_response):
        """
        Implements the authentication logic.

        :param environ: WSGI environment instance.
        :type environ: dict
        :param start_response: WSGI start response callable.
        :type start_response: callable
        :returns: True on success, False on failure
        :rtype: bool
        """
        user, passwd = decode_basic_auth(
            self.logger,
            environ.get('HTTP_AUTHORIZATION'))
        if user is not None and passwd is not None:
            if user in self._data.keys():
                self.logger.debug('User {0} found in datastore.'.format(user))
                if self.check_authentication(user, passwd):
                    return True  # Authentication is good

        # Forbid by default
        return False


PluginClass = HTTPBasicAuth
