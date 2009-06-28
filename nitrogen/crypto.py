'''Crypto module.'''

import base64
import hashlib
from subprocess import Popen, PIPE
import StringIO
import time
import os

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

def timed_hash(input, salt=None, min_time=0.01, min_cycles=2**10, trials=5, _inner=False):
    """Hashes the input with a random salt a number of times until enough
    time has elapsed.
    
    The result is of the form (68 bytes):
        [ 32 bytes of salt ][ 32 bytes of hash ][ 4 bytes of num of cycles ]
    
    Input and output should be in raw binary.
    
    Examples:
    
        >>> hash = timed_hash('password')
        >>> len(hash)
        68
        >>> hash == timed_hash('password', hash)
        True
        >>> hash == timed_hash('different', hash)
        False
        
    """
    
    cycles = None
    if salt and len(salt) == 32 + 32 + 4:
        salt_in = salt
        salt = salt_in[0:32]
        cycles = int(salt_in[-4:].encode('hex'), 16)
    else:
        # generate a salt
        salt = sha256(os.urandom(512)).digest()
    
    if not cycles and not _inner:
        # We need to run a couple trials
        hashes = [timed_hash(
            input=input,
            min_time=min_time,
            min_cycles=min_cycles,
            trials=trials,
            _inner=True) for x in range(trials)]
        count, salt, hash = list(reversed(sorted(hashes)))[0]
        return '%s%s%s' % (salt, hash, ('%08x' % count).decode('hex'))
    
    hash = input
    start_time = time.time()
    count = 0
    while True:
        if cycles is not None:
            if not cycles:
                break
            cycles -= 1
        elif count >= min_cycles and (time.time() - start_time) >= min_time:
            break
        count += 1
        hash = sha256(salt + hash).digest()
    
    if _inner:
        return (count, salt, hash)
    
    return '%s%s%s' % (salt, hash, ('%08x' % count).decode('hex'))









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