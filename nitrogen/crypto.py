'''Crypto module.'''

from subprocess import Popen, PIPE
import base64
import hashlib
import os
import StringIO
import time


def base64_encode(data, urlsafe=False):
    return base64.b64encode(data, '-_' if urlsafe else None)

def base64_decode(data):
    return base64.b64decode(s.replace('-', '+').replace('_', '/'))

base16_encode = base64.b16encode
base16_decode = lambda data: base64.b16decode(data, True)

# Setup the hash functions.
for algo in 'md5 sha1 sha224 sha256 sha384 sha512'.split():
    globals()[algo] = getattr(hashlib, algo)

# Padding functions for compatibility with OpenSSL padding
def pkcs5(string, blocksize):
    pad = blocksize - (len(string) % blocksize)
    return pad + chr(pad) * pad
def unpkcs5(string):
    pad = ord(string[-1])
    return string[:-pad]

def timed_hash(input, to_check=None, min_time=0.033, _inner=False):
    """Hashes the input with a random salt a number of times until enough
    time has elapsed.
    
    The result is of the form (68 bytes):
        1 byte - version
        32 bytes - salt
        32 bytes - hash
        4 bytes - num of cycles
    
    Input and output should be in raw binary.
    
    Examples:
    
        >>> hash = timed_hash('password')
        >>> len(hash)
        69
        >>> hash == timed_hash('password', hash)
        True
        >>> hash == timed_hash('different', hash)
        False
        
        >>> hash == timed_hash(u'password', hash)
        True
        
    """
    
    if isinstance(input, unicode):
        input = input.encode('utf8')
    
    min_cycles=2**12
    inner_trial_count=3
    
    cycle_count = None
    if to_check and len(to_check) == 32 + 32 + 4 + 1:
        version = ord(to_check[0])
        assert version == 1
        to_check = to_check[1:]
        salt = to_check[0:32]
        cycle_count = int(to_check[-4:].encode('hex'), 16)
    else:
        to_check = None
        salt = sha256(os.urandom(512)).digest()
    
    # If we are building up a new hash...
    if to_check is None and not _inner:
        
        # We need to run a couple trials
        hashes = [timed_hash(
            input=input,
            min_time=min_time,
            _inner=True) for x in range(inner_trial_count)]
        
        # Pull out the one with the most cycles.
        count, salt, hash = list(reversed(sorted(hashes)))[0]
        
        return '%c%s%s%s' % (1, salt, hash, ('%08x' % count).decode('hex'))
    
    hash = input
    start_time = time.time()
    count = 0
    while True:
        
        # Track the number of cycles if we are verifying.
        if cycle_count is not None:
            if not cycle_count:
                break
            cycle_count -= 1
        
        # Track the time and minimum number of cycles for generating.
        elif count >= min_cycles and not count % 64 and (time.time() - start_time) >= min_time:
            break
        count += 1
        
        # Do the actual hash
        hash = sha256(salt + hash).digest()
    
    # Return to ourself.
    if _inner:    
        # print 'inner', count
        return (count, salt, hash)
    
    # print 'count', count
    return '%c%s%s%s' % (1, salt, hash, ('%08x' % count).decode('hex'))









class CryptoError(Exception):
    pass

class AES(object):
    
    def __init__(self, key, iv=None, pad=True, salt=True, base64=False):
        self.key = key
        self.iv = str(iv) if iv else chr(0) * 16
        self.pad = pad
        self.salt = salt
        self.base64 = base64
        if self.keysize not in (128, 192, 256):
            raise CryptoError('key must be 128, 192, or 256 bits')
        if len(self.iv) != 16:
            raise CryptoError('iv must be 16 bytes')
        
    @property
    def keysize(self):
        return len(self.key) * 8
    
    def encrypt(self, data):
        return self._openssl_engine(True, data)
    
    def decrypt(self, data):
        return self._openssl_engine(False, data)
    
    def _openssl_engine(self, encrypt, data):
        cmd = [
            'openssl', 'aes-%d-cbc' % self.keysize, '-e' if encrypt else '-d',
            '-k', base16_encode(self.key),
            '-iv', base16_encode(self.iv)
        ]
        if not self.pad:
            cmd.append('-nopad')
        if not self.salt:
            cmd.append('-nosalt')
        if self.base64:
            cmd.append('-a') # base 64 transcode
            cmd.append('-A') # one line
        
        if hasattr(data, 'fileno'):
            proc = Popen(cmd, stdin=data, stdout=PIPE, stderr=PIPE)
            return (proc.stdout, proc.stderr)
        else:
            out, err = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(data)
            if err:
                raise CryptoError('OpenSSL said %r' % err)
            return out

if __name__ == '__main__':
    from test import run
    run()