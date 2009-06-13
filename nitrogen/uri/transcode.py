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