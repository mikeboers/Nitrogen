
import hashlib
import hmac
import os
import time

from ..uri.query import Query


NAME_TO_HASH = {}
def register_hash(name, hash):
    NAME_TO_HASH[name] = hash

register_hash('md5', hashlib.md5)
register_hash('sha256', hashlib.sha256)


class PasswordHash(object):
    """
    
    Example:
    
        >>> h = PasswordHash()
        >>> h.set_password('password')
    
        >>> h.check_password('password')
        True
        >>> h.check_password('wrong')
        False
        
        Verifying version 1.
        
        >>> h = PasswordHash('v=1.0&type=sha256&iter=4716&salt=78101bf4c50e5c359282feadf4eac583bbdf100fcfff15a7760c307c791ea4be&hash=db1d24423c1af72a7df6b48fc91f65c95de968884cb6a812368436e31dd52ada')
        >>> h.check_password('password')
        True
        >>> h.check_password('wrong')
        False
        >>> h.should_regenerate()
        False
        
    
    """
    def __init__(self, state=None, hash_name='sha256', min_time=0.01,
        min_iter=1024):
        
        self.min_time = min_time
        self.min_iter = min_iter
        self.hash_name = hash_name
        
        self.num_iter = None
        self.salt = None
        self.hash = None
        self.version = None
        self.check_time = None
        
        if state:
            self.restore_state(state)
        
    def restore_state(self, state):
        
        # For compatibility with the old "timed_hash". This can be removed
        # once the rebelhouse is up to date.
        if len(state) == 69 and ord(state[0]) == 1:
            self.version = '0.1'
            self.hash_name = 'sha256'
            self.num_iter = int(state[-4:].encode('hex'), 16)
            self.salt = state[1:33]
            self.hash = state[33:65]
        else:
            query = Query(state)
            self.version = query['v']
            self.hash_name = query['type']
            self.num_iter = int(query['iter'])
            self.salt = query['salt'].decode('hex')
            self.hash = query['hash'].decode('hex')
    
    @property
    def hasher(self):
        return NAME_TO_HASH[self.hash_name]
    
    def resalt(self):
        self.salt = self.hasher(os.urandom(8192)).digest()
    
    def set_password(self, password, best_of=3):
        rounds = []
        for i in xrange(best_of):
            self._set_password(password)
            rounds.append((self.num_iter, str(self)))
        rounds.sort()
        self.restore_state(rounds[-1][1])
        
    def _set_password(self, password):
        timer = time.time
        hasher = self.hasher
        
        self.resalt()
        num_iter = 0
        start_time = timer()
        
        blob = hmac.new(self.salt, password, hasher).digest()
        while num_iter < self.min_iter or (timer() - start_time < self.min_time):
            num_iter += 1
            blob = hasher(blob).digest()
        
        self.version = '1.0'
        self.num_iter = num_iter
        self.hash = blob
    
    def check_password(self, password):
        return {
            '0.1': self._check_v0_1,
            '1.0': self._check_v1_0,
        }[self.version](password)
    
    def _check_v0_1(self, password):
        """This is the old timed_hash."""
        hasher = self.hasher
        salt = self.salt
        blob = password
        for i in xrange(self.num_iter):
            blob = hasher(salt + blob).digest()
        return blob == self.hash
        
    def _check_v1_0(self, password):
        timer = time.time
        hasher = self.hasher
        
        start_time = timer()
        
        blob = hmac.new(self.salt, password, hasher).digest()
        for i in xrange(self.num_iter):
            blob = hasher(blob).digest()
        
        self.check_time = timer() - start_time
        return blob == self.hash
    
    def should_regenerate(self):
        if self.version != '1.0':
            return True
        if self.num_iter < self.min_iter:
            return True
        # Usually this ratio is about 0.79 for passwords just generated.
        return self.check_time / self.min_time < 0.67
    
    def __str__(self):
        return str(Query([('v', self.version), ('type', self.hash_name), ('iter', self.num_iter or 0),
            ('salt', (self.salt or '').encode('hex')), ('hash', (self.hash or
            '').encode('hex'))]))
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, str(self))




def test_timed_hash_compatibility():
    
    hashes = [
        '01129802e44542fbd7eabe52691e6cdb6810865e2982daa29481a6521678faa5512fe23594997caae715b455f8bf88f647ea3ca68548981854f5094d89681f914300002fc0',
        '016291a4faf036a2030f2117e4f8e54e50f187687a8844c961d8b5f3a1b64bfde7c8b07ed179f05ce524a9bbae49690395ef9735275f330ef97a64d3b21560debc00002f40',
        '0188921cdafba1df52879f841ade086e58ff5050c0b8882f4a73df037b85820f23ec259361e226a255282fd62748d62b8c8e9793d31457f19dbdc4d36b4715f57300002f80']
    for hash in hashes:
        hash = hash.decode('hex')
        h = PasswordHash(hash)
        assert h.check_password('password')
        assert not h.check_password('wrong')
        assert h.should_regenerate()


if __name__ == '__main__':
    from ..test import run
    run()