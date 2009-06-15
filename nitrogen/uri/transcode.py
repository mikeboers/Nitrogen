"""

Encoding and decoding:

    >>> encode("This is a string.")
    'This%20is%20a%20string.'
    
    >>> encode('this/is/a/string/with/slashes')
    'this%2fis%2fa%2fstring%2fwith%2fslashes'
    
    >>> decode('this%2fis%2fa%2fstring%2fwith%2fslashes')
    'this/is/a/string/with/slashes'
    
    >>> encode('this/is/a/string/with/safe/slashes', '/')
    'this/is/a/string/with/safe/slashes'
    
    >>> all_chars = b''.join(chr(x) for x in range(256));
    >>> encoded = encode(all_chars)
    >>> encoded
    '%00%01%02%03%04%05%06%07%08%09%0a%0b%0c%0d%0e%0f%10%11%12%13%14%15%16%17%18%19%1a%1b%1c%1d%1e%1f%20%21%22%23%24%25%26%27%28%29%2a%2b%2c-.%2f0123456789%3a%3b%3c%3d%3e%3f%40ABCDEFGHIJKLMNOPQRSTUVWXYZ%5b%5c%5d%5e_%60abcdefghijklmnopqrstuvwxyz%7b%7c%7d~%7f%80%81%82%83%84%85%86%87%88%89%8a%8b%8c%8d%8e%8f%90%91%92%93%94%95%96%97%98%99%9a%9b%9c%9d%9e%9f%a0%a1%a2%a3%a4%a5%a6%a7%a8%a9%aa%ab%ac%ad%ae%af%b0%b1%b2%b3%b4%b5%b6%b7%b8%b9%ba%bb%bc%bd%be%bf%c0%c1%c2%c3%c4%c5%c6%c7%c8%c9%ca%cb%cc%cd%ce%cf%d0%d1%d2%d3%d4%d5%d6%d7%d8%d9%da%db%dc%dd%de%df%e0%e1%e2%e3%e4%e5%e6%e7%e8%e9%ea%eb%ec%ed%ee%ef%f0%f1%f2%f3%f4%f5%f6%f7%f8%f9%fa%fb%fc%fd%fe%ff'
    >>> decode(encoded) == all_chars
    True
    
"""

import urllib

GEN_DELIMS = ':/?#[]@'
SUB_DELIMS = '!$&\'()*+,;='
SAFE = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~'

def encode(string, safe=''):
    """Encode non-safe characters.
    
    Params:
        string -- The string with unsafe characters to encode.
        safe   -- Addional characters that are deemed safe.
    """
    
    safe = set(safe + SAFE)
    out = []
    for char in string:
        out.append(char if char in safe else '%%%02x' % ord(char))
    return ''.join(out)

def decode(string):
    """Decode encoded characters."""
    return urllib.unquote(string)

if __name__ == '__main__':
    import doctest
    print "Testing", __file__
    doctest.testmod()
    print "Done."