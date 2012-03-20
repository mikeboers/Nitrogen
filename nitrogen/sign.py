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
    - dumps
    - encase
    - sign_and_encode_seal
    - encrypt_and_encode_seal_json

- specific names
    - serialize_query
    - seal_query / unseal_query
    - seal_json(obj) -> converted to json and then signed
    - encrypt(key, text, **kw)
    - encrypt_json(key, text, **kw) -> encrypt then sign

- take a look at https://github.com/mitsuhiko/itsdangerous and consider using it
    - we need the older one for backwards compatibility

- consider adding `exclude_from_query` to dumps_query
    - this allows us to have some data that the signature depends upon, but isn't serialized into the final string
    - OR have an `extra` kwarg that is pulled into the

- consider renaming the module to `dumps`

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
import json
import zlib

import tomcrypt.cipher


# Build up the map we will use to determine which hash was used by the size of
# its digest.
hash_by_size = {}
algorithms = getattr(hashlib, 'algorithms', 'md5 sha1 sha256'.split())
for name in algorithms:
    hash_by_size[getattr(hashlib, name)().digest_size] = getattr(hashlib, name)


# Build up the map we will use to encode transport-unsafe characters.
_encode_seal_map = {}
for i in xrange(256):
    _encode_seal_map[chr(i)] = '$%02x' % i
for c in (string.letters + string.digits + '_-'):
    _encode_seal_map[c] = c


def _encode_seal_data(input, safe=''):
    """Encode all characters that are not URL/cookie safe.
    
    This is similar to percent-encoding, but we use a dollar sign to avoid
    collisions with it.
    
    >>> _encode_seal_data('hello')
    'hello'
    
    >>> _encode_seal_data('before.after')
    'before$2eafter'
    
    >>> _encode_seal_data('before.after', '.')
    'before.after'
    
    >>> _encode_seal_data(''.join(chr(i) for i in range(10)))
    '$00$01$02$03$04$05$06$07$08$09'
    
    """
    if safe:
        char_map = _encode_seal_map.copy()
        for c in safe:
            char_map[c] = c
    else:
        char_map = _encode_seal_map
    return ''.join(char_map[c] for c in input)


def _decode_seal_data(input):
    """Decode a dollar-encoded string.
    
    This is more accepting than _encode_seal_data; it will decode any characters that
    have been encoded, not just unsafe ones.
    
    >>> _decode_seal_data('hello')
    'hello'
    
    >>> _decode_seal_data('$00$01$02$03$04$05$06$07$08$09')
    '\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t'
    
    >>> all_bytes = ''.join(chr(i) for i in range(256))
    >>> _decode_seal_data(_encode_seal_data(all_bytes)) == all_bytes
    True
    
    """
    return re.sub(r'\$([a-fA-F0-9]{2})', lambda m: chr(int(m.group(1), 16)), input)


def _encode_seal(data, meta):
    """Serialized a data string with associated meta data.
    
    The data, and all keys and values of the meta dict MUST be byte strings.
    
    The output data is formatted like:
    
        data.key1:value1,key2:value2 [...]
    
    All characters that are not letters, digits, underscore or hyphen will be
    dollar-encoded.
    
    >>> _encode_seal('data', dict(key='value', key2='value2'))
    'data.key:value,key2:value2'
    
    >>> _encode_seal(u'data', {})
    Traceback (most recent call last):
    ...
    TypeError: data must be str; not <type 'unicode'>
    
    >>> _encode_seal('a.b', {'!@#': '$%^'})
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
        meta_parts.append((_encode_seal_data(k), _encode_seal_data(v)))
    return '%s.%s' % (_encode_seal_data(data, '.,;'), ','.join('%s:%s' % x for x in meta_parts))


def _decode_seal(data):
    """Unserialize data from _encode_seal; returns a tuple of original data and meta.
    
    >>> _decode_seal('data.key:value')
    ('data', {'key': 'value'})
    
    >>> _decode_seal('a.b.$21$40$23:$24$25$5e')
    ('a.b', {'!@#': '$%^'})
    
    >>> all_bytes = ''.join(chr(i) for i in range(256))
    >>> meta = {}
    >>> for i in range(0, 256, 16):
    ...     key = ''.join(chr(c) for c in range(i, i + 8))
    ...     val = ''.join(chr(c) for c in range(i + 8, i + 16))
    ...     meta[key] = val
    >>> out_data, out_meta = _decode_seal(_encode_seal(all_bytes, meta))
    >>> out_data == all_bytes
    True
    >>> out_meta == meta
    True
    
    """
    data, meta = data.rsplit('.', 1)
    meta = dict(map(_decode_seal_data, x.split(':')) for x in meta.split(','))
    return _decode_seal_data(data), meta

    
def _encode_query(data):
    if isinstance(data, dict):
        data = data.items()
    return urllib.urlencode(sorted(data))


def _decode_query(data):
    return dict(urlparse.parse_qsl(data))


def _encode_binary(data):
    """Encode binary data into a transport safe form."""
    return base64.urlsafe_b64encode(data).rstrip('=')


def _decode_binary(data):
    # Fix base64 padding.
    pad_size = len(data) % 4
    if pad_size:
        data += ((4 - pad_size) * '=')
    # Must cast to string for decode.
    return base64.urlsafe_b64decode(str(data))


def _encode_int(value):
    return base64.urlsafe_b64encode(struct.pack('>I', int(value))).rstrip('=').lstrip('A')


def _decode_int(value):
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
    encoded with base64 via _encode_int.
    
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
        sig['t'] = _encode_int(time.time())
    if max_age:
        sig['x'] = _encode_int(time.time() + max_age)
    if nonce:
        sig['n'] = _encode_binary(os.urandom(nonce))
    sig['s'] = _encode_binary(hmac.new(
        key,
        _encode_seal(data, sig),
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


def _verify(key, data, sig, hash=None, max_age=None):
        
    # Extract the old mac, and calculate the new one.
    mac = _decode_binary(sig.pop('s', ''))
    try:
        new_mac = hmac.new(
            key,
            _encode_seal(data, sig),
            hash or hash_by_size[len(mac)]
        ).digest()
    except KeyError:
        raise ValueError('unknown hash algo with length %d' % len(mac))

    _assert_str_eq(mac, new_mac)
    _assert_times(sig, max_age=max_age)
    return True


def dumps_query(key, data, add_time=True, nonce=16, max_age=None, hash=hashlib.md5):
    """Signs and encapsulates the given data.
    
    The returned value is a valid URL query.
    
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
        sig['t'] = _encode_int(time.time())
    if max_age:
        sig['x'] = _encode_int(time.time() + max_age)
    if nonce:
        sig['n'] = _encode_binary(os.urandom(nonce))
    sig['s'] = _encode_binary(hmac.new(key, _encode_query(sig), hash).digest())
    return _encode_query(sig)



def loads_query(key, encoded, strict=False, **kwargs):
    """Verify a query-based signature, and return its contained data.
    
    This will verify that the MAC contained within the signature is valid,
    and verify all timing information (if present).
    
    If in 'strict' mode, all errors will result in a raised ValueError.
    Otherwise, None will be returned on error. If the signature is valid,
    the original data will be returned.
    
    Parameters:
        str key: The key to MAC with.
        str encoded: The data to verify and extract.
        bool strict = False: Should errors be thrown, or simply return False?
        int max_age = None: Number of seconds the signature was valid.
        
    """
    try:
        return _loads_query(key, encoded, **kwargs)
    except ValueError:
        if strict:
            raise


def _loads_query(key, encoded, max_age=None):
    
    sig = _decode_query(encoded)
    
    # Extract the old mac, and calculate the new one.
    mac = _decode_binary(sig.pop('s', ''))
    try:
        new_mac = hmac.new(
            key,
            _encode_query(sig),
            hash_by_size[len(mac)]
        ).digest()
    except KeyError:
        raise ValueError('unknown hash algo with length %d' % len(mac))

    _assert_str_eq(mac, new_mac)
    _assert_times(sig, max_age=max_age)

    # Remove the rest of the signature metadata.
    for key in 'n', 't', 'x':
        sig.pop(key, None)
    
    return sig


def _assert_str_eq(mac_a, mac_b):
    
    if len(mac_a) != len(mac_b):
        raise ValueError('invalid signature')
    
    # This takes the same amount of time no matter how similar they are.
    if sum(a != b for a, b in zip(mac_a, mac_b)):
        raise ValueError('invalid signature')


def _assert_times(sig, max_age=None):
    
    # Check expiry time.
    if 'x' in sig:
        try:
            expiry_time = _decode_int(sig['x'])
        except struct.error:
            raise ValueError('malformed expiry time')
        if expiry_time < time.time():
            raise ValueError('signature has self-expired')

    # Check new max_age.
    if max_age and 't' in sig:
        try:
            creation_time = _decode_int(sig['t'])
        except struct.error:
            raise ValueError('malformed creation time')
        if creation_time + max_age < time.time():
            raise ValueError('signature has expired')





def dumps(key, data, encrypt=True, compress=None, add_time=True, nonce=16, max_age=None):
    """
    
    >>> key = '0123456789abcdef'
    
    >>> encoded = dumps(key, 'abc123', encrypt=False)
    >>> encoded #doctest: +ELLIPSIS
    'abc123.n:...,s:...,t:...'
    
    >>> loads(key, encoded)
    'abc123'
    
    >>> encoded = dumps(key, 'abc123')
    >>> encoded #doctest: +ELLIPSIS
    '....i:...,s:...'
    
    >>> loads(key, encoded)
    'abc123'
    
    
    >>> loads(key, encoded + 'extra', strict=True)
    Traceback (most recent call last):
    ...
    ValueError: invalid signature
    
    """
    
    if encrypt:
        inner_meta = {}
        outer_meta = {}    
        nonce = max(0, nonce - 16)
    else:
        inner_meta = outer_meta = {}
    
    if add_time:
        inner_meta['t'] = _encode_int(time.time())
    if max_age:
        inner_meta['x'] = _encode_int(time.time() + max_age)
    
    # Try compressing the data. Only use the compressed form if requested or
    # there is enough of a savings to justify it. If we are not encrypting then
    # the compression must also do better than the base64 encoding that would
    # be required.
    if encrypt or compress or compress is None:
        data_compressed = zlib.compress(data)
        if compress or len(data) / len(data_compressed) > (1 if encrypt else 4 / 3):
            data = data_compressed
            inner_meta['z'] = '1'

    if encrypt:

        # Pack up the inner payload.
        data = _encode_seal(data, inner_meta)
        
        # Encrypt it.
        iv = os.urandom(16)
        outer_meta['i'] = _encode_binary(iv)
        cipher = tomcrypt.cipher.aes(key, iv, mode='ctr')
        data = cipher.encrypt(data)
    
    if encrypt or 'z' in inner_meta:
        
        # Make it transport safe.
        data = _encode_binary(data)
    
    # Sign it.
    outer_meta = sign(key, data, add_time=False, nonce=nonce, hash=hashlib.sha256, sig=outer_meta)
    
    # Pack up outer payload.
    return _encode_seal(data, outer_meta)
    

def dumps_json(key, data, **kwargs):
    """
    
    >>> key = '0123456789abcdef'
    >>> sealed = dumps_json(key, range(10))
    >>> loads_json(key, sealed)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    """
    data = json.dumps(data, separators=(',', ':'))
    return dumps(key, data, **kwargs)

def loads_json(key, data, **kwargs):
    data = loads(key, data, **kwargs)
    return json.loads(data)
    

def loads(key, data, strict=False, **kwargs):
    try:
        return _loads(key, data, **kwargs)
    except ValueError:
        if strict:
            raise
    return None

def _loads(key, data, decrypt=None, max_age=None):
    
    # Unpack outer payload
    data, outer_meta = _decode_seal(data)
    
    # Verify signature.
    verify(key, data, strict=True, sig=outer_meta, hash=hashlib.sha256)
    
    if decrypt is not None and decrypt != 'i' in outer_meta:
        raise ValueError('decryption flag is wrong')
    
    # Remove base64 if encrypted or compressed.
    if 'i' in outer_meta or 'z' in outer_meta:
        data = _decode_binary(data)
    
    if 'i' in outer_meta:
        
        # Decrypt it.
        iv = _decode_binary(outer_meta['i'])
        cipher = tomcrypt.cipher.aes(key, iv, mode='ctr')
        data = cipher.decrypt(data)
        
        # Unpack up the inner payload.
        data, inner_meta = _decode_seal(data)
    
    else:
        
        inner_meta = outer_meta

    # Make sure it hasn't expired.
    _assert_times(inner_meta, max_age=max_age)
    
    # Decompress.
    if 'z' in outer_meta:
        data = zlib.decompress(data)
    
    return data





# B/C
sign_query = dumps_query
verify_query = loads_query
encode_query = _encode_query
decode_query = _decode_query





def test_legacy():
    legacy = '''
        a=1&t=TtMnGA&n=hzxEMy09cWsRdLb2-Fzoyh&s=mtiThguCFBPrcgXXdJu2iA
        a=1&t=TtMniw&n=yZWCfKD_mtp8hiA-dcNbcw&s=NRO7hJcnX-tcP9TXyqoH7Q
        a=1&t=TtMnmA&n=usLdUVZ7Ziinyc1kWsbbiv&s=zyKaDzNGktszJGS0Ge99YQ
    '''.strip().split()
    
    for query in legacy:
        print '\tsig:', query
        print '\tres:', loads_query('key', query)
        assert loads_query('key', query, strict=True) == dict(a='1')
        assert not loads_query('notthekey', query)
        assert not loads_query('key', query + 'extra')
        assert not loads_query('key', query, max_age=-1)


def test_query():
    key = 'key'
    data = dict(key='value')
    print '\tdata:', data
    pack = dumps_query(key, data)
    print '\tpack:', pack
    res = loads_query(key, pack)
    print '\tres :', res
    assert res == data
    assert not loads_query('notthekey', pack)
    assert not loads_query('key', pack + 'extra')
    assert not loads_query('key', pack, max_age=-1)


def test_manual_json():
    import json
    
    key = '0123456789abcdef'
    data = {'values': [1, 4, 8]}
    data = json.dumps(data, separators=(',', ':'), sort_keys=True)
    print '\tdata:', data
    sig = sign(key, data)
    print '\tsign:', sig
    pack = '%s?%s' % (data, _encode_query(sig))
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
    pack = '%s?%s' % (data, _encode_query(sig))
    print '\tpack:', repr(pack)
    enc = _encode_binary(tomcrypt.cipher.aes(key, iv=iv, mode='ctr').encrypt(pack)) + '?' + _encode_binary(iv)
    print '\tencd:', enc

        
