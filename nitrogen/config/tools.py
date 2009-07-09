import collections

class Server(collections.Mapping):
    def __init__(self, **kwargs):
        self._data = kwargs
    def __getitem__(self, key):
        return self._data[key]
    def __iter__(self):
        return iter(self._data)
    def __len__(self):
        return len(self._data)
    def __getattr__(self, key):
        return self._data.get(key)
    def __repr__(self):
        return 'Server(%s)' % ', '.join('%s=%r' % x for x in sorted(self._data.items()))