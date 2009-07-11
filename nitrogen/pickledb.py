import bsddb
from collections import MutableMapping
try:
    import cPickle as pickle
except ImportError:
    import pickle

class PickleDB(MutableMapping):
    def __init__(self, db):
        self._db = db
    
    @staticmethod
    def _enc(value):
        return pickle.dumps(value, 2)
    
    @staticmethod
    def _dec(encoded):
        return pickle.loads(encoded)
    
    def __getitem__(self, key):
        try:
            return self._dec(self._db[self._enc(key)])
        except KeyError:
            raise KeyError(key)
        
    def __setitem__(self, key, value):
        self._db[self._enc(key)] = self._enc(value)
    
    def __delitem__(self, key):
        try:
            del self._db[self._enc(key)]
        except KeyError:
            raise KeyError(key)
    
    def __iter__(self):
        for k in self._db:
            yield self._dec(k)
    
    def __len__(self):
        return len(self._db)
    
    def __contains__(self, key):
        return self._enc(key) in self._db

class PickleHashDB(PickleDB):
    def __init__(self, *args, **kwargs):
        PickleDB.__init__(self, bsddb.hashopen(*args, **kwargs))
        
class PickleBTreeDB(PickleDB):
    def __init__(self, *args, **kwargs):
        PickleDB.__init__(self, bsddb.btopen(*args, **kwargs))

if __name__ == '__main__':
    import time
    start_time = time.time()
    
    db = PickleHashDB('test.hash')
    
    db['flickr.token'] = 'mike@example.com'
    print db['flickr.token']
    
    print '%d ms elapsed.' % (1000 * (time.time() - start_time), )