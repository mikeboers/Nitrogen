import os
import bsddb.db as bsddb
import shelve
import collections

try:
    import cPickle as pickle
except ImportError:
    import pickle

class BsddbWrapper(collections.MutableMapping):

    def __init__(self, db):
        self.db = db
        class _default(object):
            pass
        self._default = _default

    def get(self, key, default=None):
        v = self.db.get(key, self._default)
        if v is self._default:
            return default
        return v

    def __getitem__(self, key):
        v = self.db.get(key, self._default)
        if v is self._default:
            raise KeyError(v)
        return v

    def __setitem__(self, key, value):
        self.db.put(key, value)

    def __delitem__(self, key):
        self.db.delete(key)

    def __iter__(self):
        return self.db.keys()

    def __len__(self):
        return self.db.DB_length()

def open(path, name='bucket'):
    
    # Make all the directories nessesary.
    if not os.path.exists(path):
        os.makedirs(path, mode=0777)
    
    # Setup the main persistant dictionary.
    # Notice that I am NOT using
    # the shelve writeback mode, so this is unable to detect changes to mutable
    # object. You must explicity store the object again to save new state.
    env = bsddb.DBEnv()
    env.open(path, bsddb.DB_INIT_CDB | bsddb.DB_INIT_MPOOL | bsddb.DB_CREATE)
    db = bsddb.DB(env)
    db.open(name, dbtype=bsddb.DB_HASH, flags=bsddb.DB_CREATE)

    return shelve.Shelf(BsddbWrapper(db), protocol=2)


