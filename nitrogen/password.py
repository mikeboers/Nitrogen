
import hashlib
import hmac
import os
import time
import urllib
import urlparse

class PasswordHash(object):
    """
    
    basic example:
    
        >>> h = PasswordHash()
        >>> h.set('password')
    
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
    
    unicode:
        >>> h.set(u'password')
        >>> h.check(u'password')
        True
        >>> h.check(u'wrong')
        False
        
    verifying version 1.0:
        
        >>> h = PasswordHash('v=1.0&num=4716&salt=78101bf4c50e5c359282feadf4eac583bbdf100fcfff15a7760c307c791ea4be&hash=db1d24423c1af72a7df6b48fc91f65c95de968884cb6a812368436e31dd52ada')
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
        >>> h.should_reset()
        False
        
    """
    
    CURRENT_VERSION = '1.0'
    MIN_TIME = 0.25
    MIN_ITER = 2**10
    
    def __init__(self, state=None, password=None, min_time=None, min_iter=None):
        
        self.min_time = min_time or self.MIN_TIME
        self.min_iter = min_iter or self.MIN_ITER
        
        self.num_iter = None
        self.salt = None
        self.hash = None
        self.version = None
        self.check_time = None
        
        if state is not None:
            self.restore_state(state)
        
        if password is not None:
            self.set(password)
        
    def restore_state(self, state):
        
        # For compatibility with the old "timed_hash". This can be removed
        # once the rebelhouse is up to date.
        if len(state) == 69 and ord(state[0]) == 1:
            self.version = '0.1'
            self.num_iter = int(state[-4:].encode('hex'), 16)
            self.salt = state[1:33]
            self.hash = state[33:65]
        else:
            query = dict(urlparse.parse_qsl(state))
            self.version = query['v']
            self.num_iter = int(query['num'])
            self.salt = query['salt'].decode('hex')
            self.hash = query['hash'].decode('hex')
    
    def __str__(self):
        return urllib.urlencode([('v', self.version), ('num', self.num_iter or 0),
            ('salt', (self.salt or '').encode('hex')), ('hash', (self.hash or
            '').encode('hex'))]))
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, str(self))
    
    def resalt(self):
        self.salt = hashlib.sha256(os.urandom(8192)).digest()
    
    def set(self, password, best_of=1):    
        self.resalt()
        rounds = []
        password = password.encode('utf8')
        for i in xrange(best_of):
            self._set(password)
            rounds.append((self.num_iter, str(self)))
        rounds.sort()
        self.restore_state(rounds[-1][1])
        self.version = self.CURRENT_VERSION
        
    def _set(self, password):
        timer = time.time
        hasher = hashlib.sha256
        
        num_iter = 0
        end_time = timer() + self.min_time
        
        blob = hmac.new(self.salt, password, hasher).digest()
        while num_iter < self.min_iter or timer() < end_time:
            num_iter += 1
            blob = hasher(blob).digest()
        
        self.num_iter = num_iter
        self.hash = blob
    
    def check(self, password):
        start_time = time.time()
        out = {
            '0.1': self._check_v0_1,
            '1.0': self._check_v1_0,
        }[self.version](password.encode('utf8'))
        self.check_time = time.time() - start_time
        return out
    
    def _check_v0_1(self, password):
        """This is the old timed_hash.
        
        The only place this is in use will be the beta and demo sites for
        PixRay, RebelHouse, and Swisssol.
        
        """
        hasher = hashlib.sha256
        salt = self.salt
        blob = password
        for i in xrange(self.num_iter):
            blob = hasher(salt + blob).digest()
        return blob == self.hash
        
    def _check_v1_0(self, password):
        hasher = hashlib.sha256
        blob = hmac.new(self.salt, password, hasher).digest()
        for i in xrange(self.num_iter):
            blob = hasher(blob).digest()
        return blob == self.hash
    
    def should_reset(self):
        if self.version < self.CURRENT_VERSION:
            return True
        if self.num_iter < self.min_iter:
            return True
        if self.check_time is not None:    
            # Usually this ratio is about 0.80 for passwords just generated.
            # print self.check_time / self.min_time
            return self.check_time / self.min_time < 0.67


def test_old_timed_hash_compatibility():
    
    hashes = [
        '01129802e44542fbd7eabe52691e6cdb6810865e2982daa29481a6521678faa5512fe23594997caae715b455f8bf88f647ea3ca68548981854f5094d89681f914300002fc0',
        '016291a4faf036a2030f2117e4f8e54e50f187687a8844c961d8b5f3a1b64bfde7c8b07ed179f05ce524a9bbae49690395ef9735275f330ef97a64d3b21560debc00002f40',
        '0188921cdafba1df52879f841ade086e58ff5050c0b8882f4a73df037b85820f23ec259361e226a255282fd62748d62b8c8e9793d31457f19dbdc4d36b4715f57300002f80']
    for hash in hashes:
        hash = hash.decode('hex')
        h = PasswordHash(hash)
        assert h.check('password')
        assert not h.check('wrong')
        assert h.should_reset()

