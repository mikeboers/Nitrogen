"""Signatures and their verification.

This module contains a number of functions for signing text/objects, and later
verifying those signatures. Signatures contain timestamps for their creation,
and expiry times.

TODO:
- build up standard packing functions that will sign/encapsulate data.
- devise general name for them
    - pack/bundle/wrap
    - notarize
    - seal
    - encase
    - sign_and_seal
    - encrypt_and_seal_json
- specific names
    - serialize_query
    - seal_query
    - seal_json(obj) -> converted to json and then signed
    - encrypt(key, text, **kw)
    - encrypt_json(key, text, **kw) -> encrypt then sign
- take a look at https://github.com/mitsuhiko/itsdangerous and consider using it
    - we need the older one for backwards compatibility
- consider adding `exclude_from_query` to sign_query
    - this allows us to have some data that the signature depends upon, but isn't serialized into the final string
    - OR have an `extra` kwarg that is pulled into the
- consider renaming the module to `seal`
- document that creation time is public
- add encryption
    - add the creation/expiry time to the inner blob
    - don't need a salt for the signature as the IV will be random

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


hash_by_size = {}
algorithms = getattr(hashlib, 'algorithms', 'md5 sha1 sha256'.split())
for name in algorithms:
    hash_by_size[getattr(hashlib, name)().digest_size] = getattr(hashlib, name)


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
        data + '?' + encode_query(sig),
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
            data + '?' + encode_query(sig),
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


if __name__ == '__main__':


    import pickle
    import json
    import tomcrypt.cipher
    

    print 'legacy'
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
    
    
    print 'query'
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
    
    
    print 'json'
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

    
    print 'single bool'
    print '\t1?' + encode_query(sign('key', '1'))
    print '\t0?' + encode_query(sign('key', '0'))
    
        
