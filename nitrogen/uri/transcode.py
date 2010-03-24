# coding: UTF-8
u"""

TODO:
    - Devise a new encoding, primarily for internal use as it is not standard,
      that gracefully handles unicode. Bytes would go to %HH, and unicode would
      go to %uHHHH or %UHHHHHHHH. This (according to Wikipedia) has been
      rejected by the W3C.
    - Make a set of encode/decode functions which are lower level, where you
      specify precisely the syntax to use and which characters are safe. It will
      default to "%" for escaping, and letters + numbers being safe.

Encoding and decoding:

    >>> encode("This is a string.")
    'This%20is%20a%20string.'
    
    >>> encode('this/is/a/string/with/slashes')
    'this%2Fis%2Fa%2Fstring%2Fwith%2Fslashes'
    
    >>> decode('this%2fis%2fa%2fstring%2fwith%2fslashes')
    u'this/is/a/string/with/slashes'
    
    >>> encode('this/is/a/string/with/safe/slashes', '/')
    'this/is/a/string/with/safe/slashes'
    
    >>> all_chars = b''.join(chr(x) for x in range(127));
    >>> encoded = encode(all_chars)
    >>> encoded
    '%00%01%02%03%04%05%06%07%08%09%0A%0B%0C%0D%0E%0F%10%11%12%13%14%15%16%17%18%19%1A%1B%1C%1D%1E%1F%20%21%22%23%24%25%26%27%28%29%2A%2B%2C-.%2F0123456789%3A%3B%3C%3D%3E%3F%40ABCDEFGHIJKLMNOPQRSTUVWXYZ%5B%5C%5D%5E_%60abcdefghijklmnopqrstuvwxyz%7B%7C%7D~'
    >>> decode(encoded) == all_chars
    True
    
"""

import urllib

GEN_DELIMS = ':/?#[]@'
SUB_DELIMS = '!$&\'()*+,;='
SAFE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~'

CHARSET = 'utf-8'
DECODE_ERRORS = 'replace'
ENCODE_ERRORS = 'strict'

def unicoder(obj, charset=CHARSET, errors=DECODE_ERRORS):
    if isinstance(obj, unicode):
        return obj
    return unicode(str(obj), charset, errors)

def encode(string, safe='', charset=CHARSET, errors=ENCODE_ERRORS):
    """Encode non-safe characters.
    
    Params:
        string -- The string with unsafe characters to encode.
        safe   -- Addional characters that are deemed safe.
    """
    
    if isinstance(string, unicode):
        string = string.encode(charset, errors)
    safe = set(safe + SAFE)
    out = []
    for char in string:
        out.append(char if char in safe else '%%%02X' % ord(char))
    return ''.join(out)

def decode(string, charset=CHARSET, errors=DECODE_ERRORS):
    """Decode encoded characters."""
    
    return urllib.unquote(string.encode('ascii', 'ignore')).decode(charset, errors)

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)