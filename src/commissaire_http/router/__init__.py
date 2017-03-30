#!/usr/bin/env python
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
HTTP Router.
"""

import logging

from routes import Mapper


class Router(Mapper):
    """
    URL router.
    """

    #: Class level logger
    logger = logging.getLogger('Router')

    def __init__(self, optional_slash=False, *args, **kwargs):
        """
        :param optional_slash: If /'s are optional when matching directories.
        :type optional_slash: bool
        :param args: All non-keyword arguments.
        :type args: tuple
        :param kwargs: All other keyword arguments.
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)
        self._optional_slash = optional_slash

    def connect(self, *args, **kwargs):
        """
        Overrides Mapper.connect adding in support for optional slashses.

        :param args: All non-keyword arguments.
        :type args: tuple
        :param kwargs: All other keyword arguments.
        :type kwargs: dict
        """
        # Cast to a list so we can modify the args
        args = list(args)
        # If we are asked to use an optional slash then find the url_path
        # in the call. It is either the first or second element.
        if self._optional_slash:
            url_path_idx = 0
            if len(args) > 1:
                url_path_idx = 1
            # If the url path ends with a forward slash then append the
            # parameter regex for matching and store it in _.
            if args[url_path_idx].endswith('/'):
                args[url_path_idx] = args[url_path_idx][:-1] + '{_:[/]?}'
        # Call the parent connect to do the rest of the heavy lifting.
        super().connect(*args, **kwargs)

    def match(self, *args, **kwargs):
        """
        Wraps routes.Mapper.match with topic specific results.

        See http://routes.readthedocs.io/en/latest/setting_up.html

        :param args: All non-keyword arguments.
        :type args: list
        :param kwargs: All keyword arguments.
        :type kwargs: dict
        :returns: Dictionary of mapped result or None if no match.
        :rtype: dict or None
        """
        self.logger.debug(
            'Executing routes.Mapper.route with: args=%s, kwargs=%s',
            args, kwargs)
        result = super(Router, self).match(*args, **kwargs)
        self.logger.debug('Router result: %s', result)
        return result
