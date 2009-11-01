import collections
import os
import re

servers = []


class _Server(object):
    """Read-only server specification."""

    def __init__(self, **kwargs):
        self._data = kwargs

    def __getattr__(self, key):
        return self._data.get(key)

    def get(self, *args, **kwargs):
        return self._data.get(*arg, **kwargs)

    def __getitem__(self, key):
        return self._data[key]

    @property
    def admin_domain(self):
        if 'admin_domain' in self._data:
            return self._data['admin_domain']
        return 'admin.' + self.domain

    @property
    def cookie_domain(self):
        if 'cookie_domain' in self._data:
            return self._data['cookie_domain']
        return '.' + self.domain


def register_server(**kwargs):
    """Register a set of keyword arguments as a possible server that we are
    on.
    """
    server = _Server(**kwargs)
    servers.append(server)
    return server


default_server = register_server(name='default')


def get_server_by(**kwargs):
    """Find a server from those which are registered. Takes a single keyword
    argument specifying the attribute to match on.
    """

    if len(kwargs) != 1:
        raise ValueError('Can only search with one parameter.')

    key, value = kwargs.items()[0]
    possibleservers = [x for x in servers if getattr(x, key) == value]

    return possibleservers[0] if possibleservers else None


