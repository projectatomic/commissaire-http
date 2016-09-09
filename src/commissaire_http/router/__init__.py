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
Prototype router.
"""

import logging

import routes


class Router(routes.Mapper):
    """
    URL router.
    """

    #: Class level logger
    logger = logging.getLogger('Router')

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
            'Executing routes.Mapper.route with: args={}, kwargs={}'.format(
                args, kwargs))
        result = super(Router, self).match(*args, **kwargs)
        self.logger.debug('Router result: {}'.format(result))

        if result and result.get('topic'):
            topic = result['topic'].format(**result)
            self.logger.info('Found a topic. Routing to {}'.format(topic))
            result['topic'] = topic
        self.logger.debug('End result: {}'.format(result))
        return result
