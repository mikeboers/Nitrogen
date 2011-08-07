
import base64
import hmac
import hashlib
from urllib import urlencode as encode_query_items
from urlparse import parse_qsl as decode_query_items
import struct
import time
import os
import math


TIME_KEY = 't'
SIG_KEY = 's'
NONCE_KEY = 'n'
EXPIRY_KEY = 'x'
DATA_KEY = 'data'

def encode_items(input):
    return '.'.join('%s%s' % x for x in input)

def decode_items(input):
    return [(x[0], x[1:]) for x in input.split('.')]

def encode_int(value):
    """
    >>> encode_int(0)
    ''
    >>> encode_int(1)
    'Q'
    >>> encode_int(314159)
    'TLLw'
    """
    return base64.urlsafe_b64encode(struct.pack('>I', int(value))).rstrip('=').lstrip('A')


def decode_int(value):
    """
    >>> decode_int('')
    0
    >>> decode_int('Q')
    1
    >>> decode_int('TLLw')
    314159

    >>> t = int(time.time())
    >>> enc = encode_int(t)
    >>> dec = decode_int(enc)
    >>> t == dec
    True

    """
    value = 'A' * (6 - len(value)) + str(value) + '=='
    return struct.unpack('>I', base64.urlsafe_b64decode(value))[0]


def _signature(key, data, hash):
    return base64.b64encode(hmac.new(key, data, hash or hashlib.md5).digest(), '-_').rstrip('=')


def sign(key, data, hash=None, max_age=None, add_time=None, add_nonce=True,
    nonce_bits=128, as_query=False):
    
    encode = encode_query_items if as_query else encode_items
        
    sig_data = {}
    
    if add_time or (add_time is None and max_age is None):
        sig_data[TIME_KEY] = encode_int(time.time())
    if max_age is not None:
        sig_data[EXPIRY_KEY] = encode_int(time.time() + max_age)
    if add_nonce:
        sig_data[NONCE_KEY] = base64.urlsafe_b64encode(
            hashlib.sha256(os.urandom(1024)).digest())[
                :int(math.ceil(nonce_bits / 6))]
    
    to_sign = sig_data.copy()
    to_sign[DATA_KEY] = data
    to_sign = encode(sorted(to_sign.items()))
    sig_data[SIG_KEY] = _signature(key, to_sign, hash)
    
    return encode(sig_data.items())

def verify(key, data, signature, hash=None, max_age=None, strict=False):
    
    as_query = signature[1] == '='
    encode = encode_query_items if as_query else encode_items
    decode = decode_query_items if as_query else decode_items


    sig_data = dict(decode(signature))
    old_sig = sig_data.pop(SIG_KEY)
    sig_data[DATA_KEY] = data
    to_sign = encode(sorted(sig_data.items()))
    new_sig = _signature(key, to_sign, hash)
    
    # We are comparing every character explicitly. This is so that all of
    # the failure cases take exactly the same amount of time. Don't try
    # to "clean" this up or you might introduce a timing attack.
    if len(old_sig) != len(new_sig):
        if strict:
            raise ValueError('signature has wrong length')
        return False
    wrong_chars = 0
    for i in range(len(new_sig)):
        wrong_chars += 0 if (old_sig[i] == new_sig[i]) else 1
    if wrong_chars > 0:
        if strict:
            raise ValueError('bad signature')
        return False

    # Make sure the built in expiry time is okay.
    if EXPIRY_KEY in sig_data:
        try:
            expiry_time = decode_int(sig_data[EXPIRY_KEY])
        except struct.error:
            if strict:
                raise ValueError('bad expiry time')
            return False
        if expiry_time < time.time():
            if strict:
                raise ValueError('signature has expired')
            return False

    # Make sure it isnt too old.
    if max_age is not None and TIME_KEY in sig_data:
        try:
            creation_time = decode_int(sig_data[TIME_KEY])
        except struct.error:
            if strict:
                raise ValueError('bad creation time')
            return False
        if creation_time + max_age < time.time():
            if strict:
                raise ValueError('signature is too old')
            return False
    return True

if __name__ == '__main__':
    
    sig = sign('key', 'data', max_age=10)
    print sig
    print verify('key', 'data', sig, strict=True)
    
    sig = sign('key', 'data', max_age=10, as_query=True)
    print sig
    print verify('key', 'data', sig, strict=True)
    
    from nitrogen.uri.query import Query
    q = Query(key='value')
    q.sign('key')
    print q