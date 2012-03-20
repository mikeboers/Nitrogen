from __future__ import division

import hashlib
import hmac
import os
import time
import urllib
import urlparse

import tomcrypt.pkcs5


# This object will get be updated with tuples of (num_iters, time_to_hash) every
# time pkcs5 is used.
_pkcs5_timings = []


def _get_pkcs5_frequency():
    
    # Setup initial timings.
    while len(_pkcs5_timings) < 3:
        start_time = time.time()
        x = tomcrypt.pkcs5.pkcs5('password', salt='salt', iteration_count=1024, hash='sha256')
        _pkcs5_timings.append((1024, time.time() - start_time))
    
    return sum(n / t for n, t in _pkcs5_timings) / len(_pkcs5_timings)


def _timed_pkcs5(input, salt, duration):
    
    # Determine how many iterations we should do.
    iteration_count = int(duration * _get_pkcs5_frequency())
    
    start_time = time.time()
    
    output = tomcrypt.pkcs5.pkcs5(
        input,
        salt=salt,
        iteration_count=iteration_count,
        hash='sha256'
    )
    
    # Update our timing estimators only if we were faster than expected.
    actual_duration = time.time() - start_time
    if actual_duration < duration:
        _pkcs5_timings.append((iteration_count, actual_duration))
        _pkcs5_timings.sort(key=lambda x: x[0] / x[1])
        _pkcs5_timings[:] = _pkcs5_timings[-5:]
    
    return iteration_count, output
    

class PasswordHash(object):
    """
    
    Basic example:
    
        >>> h = PasswordHash()
        >>> h.set('password')
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
    
    Version 0.1 (RebelHouse and PixRay):
    
        >>> h = PasswordHash('01129802e44542fbd7eabe52691e6cdb6810865e2982daa29481a6521678faa5512fe23594997caae715b455f8bf88f647ea3ca68548981854f5094d89681f914300002fc0'.decode('hex'))
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
        >>> h.should_reset()
        True
        
    Version 1.0 (full Python pseudo timed PKCS5):
        
        >>> h = PasswordHash('v=1.0&num=4716&salt=78101bf4c50e5c359282feadf4eac583bbdf100fcfff15a7760c307c791ea4be&hash=db1d24423c1af72a7df6b48fc91f65c95de968884cb6a812368436e31dd52ada')
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
        >>> h.should_reset()
        True
    
    Version 2.0 (timed PKCS5)
    
        >>> h = PasswordHash('v=2.0&num=79190&salt=b2fd88056ce0cfdc8e9ef97dab90416d27a50163b093ebbf787e5cb6d4be4bd0&hash=0ce5f5abbbd0f1919e27985c963789e1808b0769a36479255bb606ae16a85381')
        >>> h.check('password')
        True
        >>> h.check('wrong')
        False
        
    """
    
    current_version = '2.0'
    min_time = 0.25
    
    def __init__(self, state=None, password=None, min_time=None):
        
        if min_time is not None:
            self.min_time = min_time

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
            '').encode('hex'))])
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, str(self))
    
    def resalt(self):
        self.salt = hashlib.sha256(os.urandom(8192)).digest()
    
    def set(self, password):

        if isinstance(password, unicode):
            password = password.encode('utf8')
        
        self.version = self.current_version
        self.resalt()
        
        self.num_iter, self.hash = _timed_pkcs5(password, self.salt, self.min_time)
    
    def check(self, password):
        start_time = time.time()
        out = {
            '0.1': self._check_v0_1,
            '1.0': self._check_v1_0,
            '2.0': self._check_v2_0,
        }[self.version](password.encode('utf8'))
        self.check_time = time.time() - start_time
        return out
    
    def _check_v0_1(self, password):
        """Used on PixRay, RebelHouse, and Swisssol."""
        hasher = hashlib.sha256
        salt = self.salt
        blob = password
        for i in xrange(self.num_iter):
            blob = hasher(salt + blob).digest()
        return blob == self.hash
        
    def _check_v1_0(self, password):
        """I'm not sure if this is actually in use anywhere."""
        hasher = hashlib.sha256
        blob = hmac.new(self.salt, password, hasher).digest()
        for i in xrange(self.num_iter):
            blob = hasher(blob).digest()
        return blob == self.hash
    
    def _check_v2_0(self, password):
        """New hotness."""
        return self.hash == tomcrypt.pkcs5.pkcs5(
            password,
            salt=self.salt,
            iteration_count=self.num_iter,
            hash='sha256'
        )
    
    def should_reset(self):
        if self.version < self.current_version:
            return True
        if self.num_iter < self.min_iter:
            return True
        if self.check_time is not None:    
            # This ratio is near 1 for passwords just generated.
            return self.check_time / self.min_time < 0.5


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        passwords = sys.argv[1:]
    else:
        import getpass
        passwords = [getpass.getpass('password: ')]
    
    for password in passwords:
        hasher = PasswordHash()
        hasher.set(password)
        print str(hasher)
    