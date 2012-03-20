"""Signatures and their verification.

This module contains a number of functions for signing text/objects, and later
verifying those signatures. Signatures contain timestamps for their creation,
and expiry times.

The signature of a string of data is the HMAC-SHA1 (by default) of:

    data + '?' + query_encode(meta)

This format asserts that if the HMACs match then the data and every component of
metadata (both keys and values) have the same length and same content.



TODO:
- build up standard packing functions that will sign/encapsulate data.
- devise general name for them

    - pack/bundle/wrap
    - notarize
    - seal
    - encase
    - sign_and_seal_dumps
    - encrypt_and_seal_dumps_json

- specific names
    - serialize_query
    - seal_query / unseal_query
    - seal_json(obj) -> converted to json and then signed
    - encrypt(key, text, **kw)
    - encrypt_json(key, text, **kw) -> encrypt then sign

- take a look at https://github.com/mitsuhiko/itsdangerous and consider using it
    - we need the older one for backwards compatibility

- consider adding `exclude_from_query` to sign_query
    - this allows us to have some data that the signature depends upon, but isn't serialized into the final string
    - OR have an `extra` kwarg that is pulled into the

- consider renaming the module to `seal`

- document that creation time is public for signatures

- add encryption
    - add the creation/expiry time to the inner blob
    - don't need a salt for the signature as the IV will be random

- userinfo/path/query safe characters:
    
    - !!! see what characters are cookie safe
     
    3.4: query = *( pchar / "/" / "?" )
    3.3: (path) segment       = *pchar
         pchar = unreserved / pct-encoded / sub-delims / ":" / "@"
    2.3: unreserved  = ALPHA / DIGIT / "-" / "." / "_" / "~"
    2.2: sub-delims  = "!" / "$" / "&" / "'" / "(" / ")"
                  / "*" / "+" / "," / ";" / "="
    
    a-zA-Z0-9_- are taken by base64
    &= are taken by standard queries
    ; is often interpreted same as & in queries
    + is interpreted as a space
    
    leaves: !$'()*+,;.~
    
    data ";" key "." value *("," key2 "." value2)
    
    data;(iv)012345(x)012345
    data;iv.012345,x.012345
    data;iv$012345,x$012345
    data.iv,012345;x,012345
    data$iv,012345;x,012345
    data!iv,012345;x,012345 (this often doesnt work)
    data.iv:012345,x:012345 <<<
    
    dollar-encode the rest
    
    
    
    

"""

from __future__ import division

import hashlib
import struct
import hmac
import datetime
import os
import urlparse
import urllib
import base64
import time
import string
import re


# Build up the map we will use to determine which hash was used by the size of
# its digest.
hash_by_size = {}
algorithms = getattr(hashlib, 'algorithms', 'md5 sha1 sha256'.split())
for name in algorithms:
    hash_by_size[getattr(hashlib, name)().digest_size] = getattr(hashlib, name)


# Build up the map we will use to encode transport-unsafe characters.
_dollar_encode_map = {}
for i in xrange(256):
    _dollar_encode_map[chr(i)] = '$%02x' % i
for c in (string.letters + string.digits + '_-'):
    _dollar_encode_map[c] = c


def _dollar_encode(input, safe=''):
    """Encode all characters that are not URL/cookie safe.
    
    This is similar to percent-encoding, but we use a dollar sign to avoid
    collisions with it.
    
    >>> _dollar_encode('hello')
    'hello'
    
    >>> _dollar_encode('before.after')
    'before$2eafter'
    
    >>> _dollar_encode('before.after', '.')
    'before.after'
    
    >>> _dollar_encode(''.join(chr(i) for i in range(10)))
    '$00$01$02$03$04$05$06$07$08$09'
    
    """
    if safe:
        char_map = _dollar_encode_map.copy()
        for c in safe:
            char_map[c] = c
    else:
        char_map = _dollar_encode_map
    return ''.join(char_map[c] for c in input)


def _dollar_decode(input):
    """Decode a dollar-encoded string.
    
    This is more accepting than _dollar_encode; it will decode any characters that
    have been encoded, not just unsafe ones.
    
    >>> _dollar_decode('hello')
    'hello'
    
    >>> _dollar_decode('$00$01$02$03$04$05$06$07$08$09')
    '\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t'
    
    >>> all_bytes = ''.join(chr(i) for i in range(256))
    >>> _dollar_decode(_dollar_encode(all_bytes)) == all_bytes
    True
    
    """
    return re.sub(r'\$([a-fA-F0-9]{2})', lambda m: chr(int(m.group(1), 16)), input)


def _seal_dumps(data, meta):
    """Serialized a data string with associated meta data.
    
    The data, and all keys and values of the meta dict MUST be byte strings.
    
    The output data is formatted like:
    
        data.key1:value1,key2:value2 [...]
    
    All characters that are not letters, digits, underscore or hyphen will be
    dollar-encoded.
    
    >>> _seal_dumps('data', dict(key='value', key2='value2'))
    'data.key:value,key2:value2'
    
    >>> _seal_dumps(u'data', {})
    Traceback (most recent call last):
    ...
    TypeError: data must be str; not <type 'unicode'>
    
    >>> _seal_dumps('a.b', {'!@#': '$%^'})
    'a.b.$21$40$23:$24$25$5e'
    
    """
    if not isinstance(data, str):
        raise TypeError('data must be str; not %r' % type(data))
    meta_parts = []
    for k, v in sorted(meta.iteritems()):
        if not isinstance(k, str):
            raise TypeError('meta key %r must be str; not %r' % (k, type(k)))
        if not isinstance(v, str):
            raise TypeError('meta %r value %r must be str; not %r' % (k, v, type(v)))
        meta_parts.append((_dollar_encode(k), _dollar_encode(v)))
    return '%s.%s' % (_dollar_encode(data, '.,;'), ','.join('%s:%s' % x for x in meta_parts))


def _seal_loads(data):
    """Unserialize data from _seal_dumps; returns a tuple of original data and meta.
    
    >>> _seal_loads('data.key:value')
    ('data', {'key': 'value'})
    
    >>> _seal_loads('a.b.$21$40$23:$24$25$5e')
    ('a.b', {'!@#': '$%^'})
    
    >>> all_bytes = ''.join(chr(i) for i in range(256))
    >>> meta = {}
    >>> for i in range(0, 256, 16):
    ...     key = ''.join(chr(c) for c in range(i, i + 8))
    ...     val = ''.join(chr(c) for c in range(i + 8, i + 16))
    ...     meta[key] = val
    >>> out_data, out_meta = _seal_loads(_seal_dumps(all_bytes, meta))
    >>> out_data == all_bytes
    True
    >>> out_meta == meta
    True
    
    """
    data, meta = data.rsplit('.', 1)
    meta = dict(map(_dollar_decode, x.split(':')) for x in meta.split(','))
    return _dollar_decode(data), meta

    
def encode_query(data):
    if isinstance(data, dict):
        data = data.items()
    return urllib.urlencode(sorted(data))


def decode_query(data):
    return dict(urlparse.parse_qsl(data))


def encode_binary(data):
    """Encode binary data into a transport safe form."""
    return base64.urlsafe_b64encode(data).rstrip('=')


def decode_binary(data):
    # Fix base64 padding.
    pad_size = len(data) % 4
    if pad_size:
        data += ((4 - pad_size) * '=')
    # Must cast to string for decode.
    return base64.urlsafe_b64decode(str(data))


def encode_int(value):
    return base64.urlsafe_b64encode(struct.pack('>I', int(value))).rstrip('=').lstrip('A')


def decode_int(value):
    value = 'A' * (6 - len(value)) + str(value) + '=='
    return struct.unpack('>I', base64.urlsafe_b64decode(value))[0]


def sign(key, data, add_time=True, nonce=16, max_age=None, hash=hashlib.sha1, sig={}):
    """Calculate a signature for the given data.
    
    The returned signature is a dict with the following keys:
        s: signature
        n: nonce
        t: signing time
        x: expiry time
    
    Only the signature will always be there, with the reset depending upon other
    arguments to this function. All keys and values are guarunteed to be URL
    safe. Times are represented as the number of seconds since the epoch,
    encoded with base64 via encode_int.
    
    Parameters:
        str key: The key to MAC with.
        str data: The data to sign.
        bool add_time = True: Should the current time be added to the signature? 
        int nonce = 16: Length of the nonce to be added; 0 implies no nonce.
        int max_age = None: Number of seconds that this signature is valid.
        obj hash = hashlib.sha1: Hash algorithm to use.
        dict sig = {}: Other data to add to the signature.
    
    """
    sig = sig.copy()
    if add_time:
        sig['t'] = encode_int(time.time())
    if max_age:
        sig['x'] = encode_int(time.time() + max_age)
    if nonce:
        sig['n'] = encode_binary(os.urandom(nonce))
    sig['s'] = encode_binary(hmac.new(
        key,
        _seal_dumps(data, sig),
        hash
    ).digest())
    return sig


def verify(key, data, sig, strict=False, **kwargs):
    """Verify a signature for the given data.
    
    This will verify that the MAC contained within the signature is valid,
    and verify all timing information (if present).
    
    If in 'strict' mode, all errors will result in a raised ValueError.
    Otherwise, False will be returned on error. If the signature is valid,
    True will be returned.
    
    Parameters:
        str key: The key to MAC with.
        str data: The data to verify the signature of.
        dict sig: The signature to verify.
        bool strict = False: Should errors be thrown, or simply return False?
        int max_age = None: Number of seconds the signature was valid.
        
    """
    # Copy sig OR coerce to a dict.
    sig = dict(sig)
    try:
        return _verify(key, data, sig, **kwargs)
    except ValueError:
        if strict:
            raise
    return False


def _verify(key, data, sig, **kwargs):
        
    # Extract the old mac, and calculate the new one.
    mac = decode_binary(sig.pop('s', ''))
    try:
        new_mac = hmac.new(
            key,
            _seal_dumps(data, sig),
            hash_by_size[len(mac)]
        ).digest()
    except KeyError:
        raise ValueError('unknown hash algo with length %d' % len(mac))

    _assert_str_eq(mac, new_mac)
    _assert_times(sig, **kwargs)
    return True


def sign_query(key, data, add_time=True, nonce=16, max_age=None, hash=hashlib.md5):
    """Signs and encapsulates the given data.
    
    The returned value is guarunteed to be URL safe.
    
    Parameters:
        str key: The key to MAC with.
        dict data: The data to sign; all keys/values MUST be strings.
        bool add_time = True: Should the current time be added to the signature? 
        int nonce = 16: Length of the nonce to be added; 0 implies no nonce.
        int max_age = None: Number of seconds that this signature is valid.
        obj hash = hashlib.md5: Hash algorithm to use.
    
    """
    sig = dict(data)
    if add_time:
        sig['t'] = encode_int(time.time())
    if max_age:
        sig['x'] = encode_int(time.time() + max_age)
    if nonce:
        sig['n'] = encode_binary(os.urandom(nonce))
    sig['s'] = encode_binary(hmac.new(key, encode_query(sig), hash).digest())
    return encode_query(sig)


def verify_query(key, encoded, strict=False, **kwargs):
    """Verify a query-based signature, and return its contained data.
    
    This will verify that the MAC contained within the signature is valid,
    and verify all timing information (if present).
    
    If in 'strict' mode, all errors will result in a raised ValueError.
    Otherwise, False will be returned on error. If the signature is valid,
    True will be returned.
    
    Parameters:
        str key: The key to MAC with.
        str encoded: The data to verify and extract.
        bool strict = False: Should errors be thrown, or simply return False?
        int max_age = None: Number of seconds the signature was valid.
        
    """
    try:
        return _verify_query(key, encoded, **kwargs)
    except ValueError:
        if strict:
            raise


def _verify_query(key, encoded, **kwargs):
    
    sig = decode_query(encoded)
    
    # Extract the old mac, and calculate the new one.
    mac = decode_binary(sig.pop('s', ''))
    try:
        new_mac = hmac.new(
            key,
            encode_query(sig),
            hash_by_size[len(mac)]
        ).digest()
    except KeyError:
        raise ValueError('unknown hash algo with length %d' % len(mac))

    _assert_str_eq(mac, new_mac)
    _assert_times(sig, **kwargs)

    # Remove the rest of the signature metadata.
    for key in 'n', 't', 'x':
        sig.pop(key, None)
    
    return sig


def _assert_str_eq(mac_a, mac_b):
    
    if len(mac_a) != len(mac_b):
        raise ValueError('incomplete signature')
    
    # This takes the same amount of time no matter how similar they are.
    if sum(a != b for a, b in zip(mac_a, mac_b)):
        raise ValueError('invalid signature')


def _assert_times(sig, max_age=None):
    
    # Check expiry time.
    if 'x' in sig:
        try:
            expiry_time = decode_int(sig['x'])
        except struct.error:
            raise ValueError('malformed expiry time')
        if expiry_time < time.time():
            raise ValueError('signature has self-expired')

    # Check new max_age.
    if max_age and 't' in sig:
        try:
            creation_time = decode_int(sig['t'])
        except struct.error:
            raise ValueError('malformed creation time')
        if creation_time + max_age < time.time():
            raise ValueError('signature has expired')



def test_legacy():
    legacy = '''
        a=1&t=TtMnGA&n=hzxEMy09cWsRdLb2-Fzoyh&s=mtiThguCFBPrcgXXdJu2iA
        a=1&t=TtMniw&n=yZWCfKD_mtp8hiA-dcNbcw&s=NRO7hJcnX-tcP9TXyqoH7Q
        a=1&t=TtMnmA&n=usLdUVZ7Ziinyc1kWsbbiv&s=zyKaDzNGktszJGS0Ge99YQ
    '''.strip().split()
    
    for query in legacy:
        print '\tsig:', query
        print '\tres:', verify_query('key', query)
        assert verify_query('key', query, strict=True) == dict(a='1')
        assert not verify_query('notthekey', query)
        assert not verify_query('key', query + 'extra')
        assert not verify_query('key', query, max_age=-1)


def test_query():
    key = 'key'
    data = dict(key='value')
    print '\tdata:', data
    pack = sign_query(key, data)
    print '\tpack:', pack
    res = verify_query(key, pack)
    print '\tres :', res
    assert res == data
    assert not verify_query('notthekey', pack)
    assert not verify_query('key', pack + 'extra')
    assert not verify_query('key', pack, max_age=-1)


def test_manual_json():
    import json
    
    key = '0123456789abcdef'
    data = {'values': [1, 4, 8]}
    data = json.dumps(data, separators=(',', ':'), sort_keys=True)
    print '\tdata:', data
    sig = sign(key, data)
    print '\tsign:', sig
    pack = '%s?%s' % (data, encode_query(sig))
    print '\tpack:', pack
    good = verify(key, data, sig)
    print '\tgood:', good
    assert good
    assert not verify('notthekey', data, sig)
    assert not verify('key', data + 'extra', sig)
    assert not verify('key', data, sig, max_age=-1)


def test_manual_encrypted_pickle():
    import pickle
    import tomcrypt.cipher
    
    print 'encrypted pickle'
    key = '0123456789abcdef'
    iv = os.urandom(tomcrypt.cipher.aes.block_size)
    data = {'values': [1, 4, 8]}
    data = pickle.dumps(data)
    print '\tdata:', repr(data)
    sig  = sign(key, data)
    print '\tsign:', sig
    pack = '%s?%s' % (data, encode_query(sig))
    print '\tpack:', repr(pack)
    enc = encode_binary(tomcrypt.cipher.aes(key, iv=iv, mode='ctr').encrypt(pack)) + '?' + encode_binary(iv)
    print '\tencd:', enc

        
