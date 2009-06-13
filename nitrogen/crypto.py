'''Crypto module.'''

import base64
import hashlib
from subprocess import Popen, PIPE
import StringIO

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
    import doctest
    doctest.testmod()
    
    aes = AES('thisisakey..yeah', pad=True, salt=True, base64=True)
    enc = aes.encrypt('This is some secret data.')
    print enc, aes.decrypt(enc)