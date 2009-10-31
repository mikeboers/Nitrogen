bucket_sessions = {}
bucket_classes = {}
def Bucket(name, auto_commit=True):
    
    if name in bucket_classes:
        return bucket_classes[name]()
    
    def _Session():
        thread = threading.current_thread()
        if thread not in bucket_sessions:
            bucket_sessions[thread] = Session()
        return bucket_sessions[thread]
    
    item_table = Table(name, Base.metadata,
        Column('id', Integer, primary_key=True),
        Column('_key', String),
        Column('_value', String),
        Column('_expiry', Float)
    )

    class Expired(KeyError):
        pass
    
    class Item(object):
        __tablename__ = name
        
        def __init__(self, key):
            self._key = pickle.dumps(key)
            self._public_key = key
            self._expired = False
        
        @reconstructor
        def __reconstruct__(self):
            # Expire self
            self._public_key = pickle.loads(str(self._key))
            self._expired = False
            if self._expiry and self._expiry < time.time():
                self.delete()
        
        def delete(self):
            s = _Session()
            s.delete(self)
            s.commit()
            self._expired = True
        
        @property
        def expired(self):
            return self._expired
        
        @property
        def key(self):
            return self._public_key
        
        @property
        def value(self):
            return pickle.loads(str(self._value))
        
        @value.setter
        def value(self, value):
            self._value = pickle.dumps(value)
        
        @property
        def expiry(self):
            return self._expiry
        
        @expiry.setter
        def expiry(self, expiry):
            if expiry is True:
                expiry = -1
            elif expiry is False:
                expiry = None
            ctime = time.time()
            if expiry is not None:
                expiry = float(expiry)
                if expiry < ctime:
                    expiry += ctime
            self._expiry = expiry
            
    mapper(Item, item_table)
    item_table.create(engine, checkfirst=True)
    
    
    
    class Container(object):
        
        def _get(self, key):
            item = _Session().query(Item).filter(item_table.c._key == pickle.dumps(key)).first()
            if item and not item.expired:
                return item
            return None
        
        def __getitem__(self, key):
            item = self._get(key)
            if item is None:
                raise KeyError(key)
            # str wrapping due to unicode returns.
            return item.value
        
        def get(self, key, default=None):
            try:
                return self[key]
            except KeyError:
                return default
        
        def set(self, key, value, *args):
            
            # Asserting that it is hashable.
            # This is making us more like a "normal" dictionary.
            hash(key)
            
            s = _Session()
            item = self._get(key) or Item(key)
            item.value = value
            if args:
                item.expiry = args[0]
            if not item.id:
                s.add(item)
            s.commit()
        
        __setitem__ = set
        
        def __delitem__(self, key):
            item = self._get(key)
            if item and not item.expired:
                item.delete()
        
        def __contains__(self, key):
            return self._get(key) is not None
        
        def iterkeys(self):
            for item in _Session().query(Item).all():
                if not item.expired:
                    yield item.key
        
        __iter__ = iterkeys
    
    bucket_classes[name] = Container
    return Container()
