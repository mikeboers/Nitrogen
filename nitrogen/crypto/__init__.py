'''Crypto module.'''

from subprocess import Popen, PIPE
import logging

from .password import PasswordHash


log = logging.getLogger(__name__)







# Padding functions for compatibility with OpenSSL padding
def pkcs5(string, blocksize):
    pad = blocksize - (len(string) % blocksize)
    return pad + chr(pad) * pad
def unpkcs5(string):
    pad = ord(string[-1])
    return string[:-pad]


def timed_hash(password, state=None):
    """For backwards compatibility. Uses the new methods, but is able to check
    against the old ones.
    
    Original docs as follows:
    
    Hashes the input with a random salt a number of times until enough
    time has elapsed.
    
    The result is of the form (68 bytes):
        1 byte - version
        32 bytes - salt
        32 bytes - hash
        4 bytes - num of cycles
    
    Input and output should be in raw binary.
    
    Examples:
    
        >>> hash = timed_hash('password')
        >>> hash == timed_hash('password', hash)
        True
        >>> hash == timed_hash('different', hash)
        False
        
        >>> hash == timed_hash(u'password', hash)
        True
        
    """
    
    log.warning('timed_hash is depreciated')
    h = PasswordHash(state)
    if state is not None:
        if h.check_password(password):
            return state
        return None
    h.set_password(password)
    return str(h)
    

class CryptoError(Exception):
    pass

class OpenSSLError(CryptoError):
    pass


class AES(object):
    """AES encryptor.
    
    Example:
    
        >>> aes = AES('0123456789abcdef', pad=True, base64=True)
        >>> aes.encrypt('Hello, world!')
        'U35iwIjove8a5guo1sEjSg=='
        >>> aes.decrypt('U35iwIjove8a5guo1sEjSg==')
        'Hello, world!'
        
        >>> aes.decrypt('bad length')
        Traceback (most recent call last):
        ...
        OpenSSLError: bad decrypt; 0606506D:digital envelope routines:EVP_DecryptFinal_ex:wrong final block length
        
        >>> aes.decrypt('U35iwIlove8a5guo1sEjSg==')
        Traceback (most recent call last):
        ...
        OpenSSLError: bad decrypt; 06065064:digital envelope routines:EVP_DecryptFinal_ex:bad decrypt
    
    """
    def __init__(self, key, iv=None, pad=False, salt=False, base64=False):
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
            '-k', self.key.encode('hex'),
            '-iv', self.iv.encode('hex')
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
                errors = []
                for raw_error in err.strip().splitlines():
                    error = raw_error.split(':')
                    if len(error) >= 6 and error[1] == 'error':
                        # error_id     = error[2] # Can lookup with `openssl errstr <id>`
                        # error_module = error[3]
                        # error_func   = error[4]
                        # error_msg    = error[5]
                        # errors.append('%s:%s:%s' % (error_id, error_module, error_msg))
                        errors.append(':'.join(error[2:6]))
                    else:
                        errors.append(raw_error.strip())                 
                raise OpenSSLError('; '.join(errors))
            return out


if __name__ == '__main__':
    from ..test import run
    run()