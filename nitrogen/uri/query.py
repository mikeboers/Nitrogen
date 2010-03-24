# coding: UTF-8
u"""Module for a URI query parser.

It has dictionary like access. While this class will accept more than one
value per key (a key can be repeated) the dictionary methods will tend to
return only the first of those values. Care has been taken, however, to always
maintain the order of the multiple values.

I need to decode + as a space, because that is what firefox does to me. I
won't, however, re-encode it as a space. It feels wrong to me.

TODO:
    - Figure out definitively if a space should be encoded to "+" or "%20".
        - See what firefox does when I enter "+" vs " " vs "%20".

Instantiate with a string:

    >>> query = Query('key1=value1&key2=value2')
    >>> query.items()
    [(u'key1', u'value1'), (u'key2', u'value2')]

Instantiate with a dict:

    >>> query = Query({u'a': 1, u'b': 2})
    >>> sorted(query.allitems())
    [(u'a', u'1'), (u'b', u'2')]

Instantiate with keyword arguments:

    >>> query = Query(a=1, b=2, c=3)
    >>> sorted(query.allitems())
    [(u'a', u'1'), (u'b', u'2'), (u'c', u'3')]

Instantiate with a list of pairs:

    >>> query = Query([('one', u'1'), ('two', u'2')])
    >>> query.allitems()
    [(u'one', u'1'), (u'two', u'2')]

Cast back to a string:
    >>> str(query)
    'one=1&two=2'

It can deal with multiple values per key (although by all the normal dict
methods it does not appear this way).:

    >>> query = Query('key=value1&key=value2')
    >>> query['key']
    u'value1'
    >>> len(query)
    1

    >>> query.getall('key')
    [u'value1', u'value2']

    >>> query.allitems()
    [(u'key', u'value1'), (u'key', u'value2')]

Order is maintained very precisely, even with multiple values per key:

    >>> query = Query('a=1&b=2&a=3')
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'a', u'3')]

Setting is a little more difficult. Assume that unless something that extends
a tuple or list (ie passes isinstance(input, (tuple, list))) it is supposed to
be the ONLY string value for that key.

    >>> # Notice that we are still using the query with multiple values for a.
    >>> query.getall(u'a')
    [u'1', u'3']
    >>> query[u'a'] = 'value'
    >>> query.getall(u'a')
    [u'value']

Setting a list:

    >>> query.setall('key', 'a b c'.split())
    >>> query.getall('key')
    [u'a', u'b', u'c']

You can provide a sequence that is not a tuple or list by using the setall
method. This will remove all existing pairs by key, and append the new ones
on the end of the query.

    >>> def g():
    ...     for x in [1, 2, 3]:
    ...         yield x
    >>> query.setall('key', g())
    >>> query.getall('key')
    [u'1', u'2', u'3']

The query can be sorted via list.sort (notice that the key function is passed
a key/value tuple):

    >>> query = Query('a=1&c=2&b=3')
    >>> query.sort()
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'3'), (u'c', u'2')]
    >>> query.sort(key=lambda x: -ord(x[0]))
    >>> query.allitems()
    [(u'c', u'2'), (u'b', u'3'), (u'a', u'1')]

Pairs can be appended with list.append and list.insert and list.extend. (We
will just cast the values to tuples and assert they have length 2.)

    >>> query = Query()
    >>> query.append((u'a', u'1'))
    >>> query.allitems()
    [(u'a', u'1')]

    >>> query.extend(sorted({u'b': 2, u'c': 3}.items()))
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'c', u'3')]

    >>> query.insert(0, ('z', '-1'))
    >>> query.allitems()
    [(u'z', u'-1'), (u'a', u'1'), (u'b', u'2'), (u'c', u'3')]

You can update the query via dict.update:

    >>> query = Query()
    >>> query.update({u'a': 1, u'b': 2, u'c': u'4'})
    >>> query.append(('b', 3))
    >>> query.sort() # Because the dictionary does not come in order.
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2'), (u'b', u'3'), (u'c', u'4')]

    >>> query.update({u'b': '2/3'})
    >>> query.allitems()
    [(u'a', u'1'), (u'b', u'2/3'), (u'c', u'4')]

Empty queries test as false:
    >>> bool(Query())
    False
    >>> bool(Query('a=b'))
    True

Empty queries are empty:
    >>> query = Query('')
    >>> query
    Query([])
    >>> print query
    <BLANKLINE>

Parse and unparses properly

    >>> parse('key=value')
    [(u'key', u'value')]
    >>> parse('key=')
    [(u'key', u'')]
    >>> parse('key')
    [(u'key', None)]

    >>> query = Query('key')
    >>> query['a'] = None
    >>> query
    Query([(u'key', None), (u'a', None)])
    >>> str(query)
    'key&a'

    >>> query = Query('key=value/with/slashes.and.dots=and=equals')
    >>> query
    Query([(u'key', u'value/with/slashes.and.dots=and=equals')])
    >>> str(query)
    'key=value/with/slashes.and.dots=and=equals'

Unicode does work properly.
    # >>> query = Query('k%C3%A9y=%C2%A1%E2%84%A2%C2%A3%C2%A2%E2%88%9E%C2%A7%'
    # ... 'C2%B6%E2%80%A2%C2%AA%C2%BA')
    # >>> print query.keys()[0]
    # kéy
    # >>> print query[u'kéy']
    # ¡™£¢∞§¶•ªº
    #
    # >>> query = Query()
    # >>> query[u'kéy'] = u'¡™£¢∞§¶•ªº'
    # >>> print query
    # k%C3%A9y=%C2%A1%E2%84%A2%C2%A3%C2%A2%E2%88%9E%C2%A7%C2%B6%E2%80%A2%C2%AA%C2%BA

Spaces as pluses:
    >>> query = Query('key+with+spaces=value%20with%20spaces')
    >>> query
    Query([(u'key with spaces', u'value with spaces')])
    >>> str(query)
    'key+with+spaces=value+with+spaces'

Easy signatures!

    >>> query = Query('v=value')
    >>> query[u'nonce'] = '12345'
    >>> query.sign('this is the key', add_nonce=False, add_time=False)
    >>> str(query)
    'v=value&nonce=12345&_s=vDNuaJjAEWVg7Q3atnC_nA'

    >>> query.verify('this is the key')
    True
    >>> query.verify('this is not the key')
    False

    >>> query = Query('v=somevalue')
    >>> query.sign('another_key')
    >>> str(query) # doctest:+ELLIPSIS
    'v=somevalue&_t=...&_n=...&_s=...'
    >>> query.verify('another_key')
    True
    >>> query.verify('bad key')
    False
    >>> query.verify('another_key', max_age=-1)
    False
    >>> query.verify('another_key', max_age=-1, strict=True)
    Traceback (most recent call last):
    ...
    ValueError: signature is too old

    >>> query = Query(v='value')
    >>> query['_n'] = '123abc'
    >>> query.sign('key', max_age=60, add_time=True, add_nonce=False)
    >>> str(query) # doctest: +ELLIPSIS
    'v=value&_n=123abc&_t=...&_x=...&_s=...'
    >>> query.verify('key')
    True
    >>> query.verify('not the key')
    False
    >>> query.verify('not the key', strict=True)
    Traceback (most recent call last):
    ...
    ValueError: bad signature

"""

from __future__ import division

import collections
import time
import os
import hashlib
import hmac
import base64
import math
import struct

from multimap import MutableMultiMap

from .transcode import unicoder, decode as _decode, encode as _encode, CHARSET, ENCODE_ERRORS, DECODE_ERRORS


def decode(x, charset=None, errors=None):
    return _decode(x.replace('+', ' '), charset or CHARSET, errors or DECODE_ERRORS)


def encode(x, safe='', charset=None, errors=None):
    return _encode(x, safe + ' ', charset or CHARSET, errors or ENCODE_ERRORS).replace(' ', '+')


def parse(query, charset=None, errors=None):
    charset = charset or CHARSET
    errors = errors or DECODE_ERRORS
    ret = []
    if not query:
        return ret
    for pair in query.split(u'&'):
        pair = [decode(x, charset, errors) for x in pair.split(u'=', 1)]
        if isinstance(pair[0], str):
            pair = [unicoder(x, charset, errors) for x in pair]
        if len(pair) == 1:
            pair.append(None)
        ret.append(tuple(pair))
    return ret


def unparse(pairs, charset=None, errors=None):
    charset = charset or CHARSET
    errors = errors or ENCODE_ERRORS
    ret = []
    for pair in pairs:
        if pair[1] is None:
            ret.append(encode(pair[0], u'/', charset, errors))
        else:
            ret.append(encode(pair[0], u'/', charset, errors) + u'=' + encode(pair[1], '/= ', charset, errors))
    return u'&'.join(ret)


class Query(MutableMultiMap):
    
    def __init__(self, input=None, charset=None, decode_errors=None, encode_errors=None, **kwargs):
        self.charset = charset
        self.encode_errors = encode_errors
        self.decode_errors = decode_errors
        if isinstance(input, basestring):
            input = parse(input, self.charset, self.decode_errors)
        if input is not None:
            MutableMultiMap.__init__(self, input)
        else:
            MutableMultiMap.__init__(self)
        for k, v in kwargs.iteritems():
            self[k] = v

    def __str__(self):
        return unparse(self._pairs)

    def _conform_key(self, key):
        if key is None:
            return None
        return unicoder(key, self.charset, self.encode_errors)

    def _conform_value(self, value):
        if value is None:
            return None
        return unicoder(value, self.charset, self.encode_errors)

    def _signature(self, key, hasher):
        return base64.b64encode(hmac.new(key, str(self), hasher or hashlib.md5).digest(), '-_').rstrip('=')

    @staticmethod
    def _encode_float(value):
        """
        >>> Query._encode_float(0)
        'AAAAAAAAAAA'
        >>> Query._encode_float(1)
        'AAAAAAAA8D8'
        >>> Query._encode_float(3.14159)
        'boYb8PkhCUA'
        >>> Query._encode_float(1254784638.37394)
        'ou6Xn5-y0kE'

        """
        return base64.urlsafe_b64encode(struct.pack('d', value)).rstrip('=')

    @staticmethod
    def _decode_float(value):
        """

        >>> Query._decode_float('AAAAAAAAAAA')
        0.0
        >>> Query._decode_float('AAAAAAAA8D8')
        1.0
        >>> Query._decode_float(u'boYb8PkhCUA') # doctest: +ELLIPSIS
        3.1415...
        >>> Query._decode_float('ou6Xn5-y0kE') # doctest: +ELLIPSIS
        1254784638.37...

        >>> t = time.time()
        >>> enc = Query._encode_float(t)
        >>> dec = Query._decode_float(enc)
        >>> dec - t < 0.0001
        True

        """
        return struct.unpack('d', base64.urlsafe_b64decode(str(value) + '='))[0]

    @staticmethod
    def _encode_int(value):
        """
        >>> Query._encode_int(0)
        ''
        >>> Query._encode_int(1)
        'Q'
        >>> Query._encode_int(314159)
        'TLLw'
        """
        return base64.urlsafe_b64encode(struct.pack('>I', int(value))).rstrip('=').lstrip('A')

    @staticmethod
    def _decode_int(value):
        """
        >>> Query._decode_int('')
        0
        >>> Query._decode_int('Q')
        1
        >>> Query._decode_int('TLLw')
        314159

        >>> t = int(time.time())
        >>> enc = Query._encode_int(t)
        >>> dec = Query._decode_int(enc)
        >>> t == dec
        True

        """
        value = 'A' * (6 - len(value)) + str(value) + '=='
        return struct.unpack('>I', base64.urlsafe_b64decode(value))[0]
    
    TIME_BASE = 1262698296
    TIME_KEY = '_t'
    SIG_KEY = '_s'
    NONCE_KEY = '_n'
    EXPIRY_KEY = '_x'
    
    def sign(self, key, hasher=None, max_age=None, add_time=None, add_nonce=True,
        nonce_bits=128, time_key=TIME_KEY, sig_key=SIG_KEY, nonce_key=NONCE_KEY,
        expiry_key=EXPIRY_KEY):

        # encode_time = lambda x: str(int(x))
        # encode_time = lambda x: '%.2f' % x
        # encode_time = self._encode_float
        encode_time = self._encode_int

        if add_time or (add_time is None and max_age is None):
            self[time_key] = encode_time(time.time() - self.TIME_BASE)
        if max_age is not None:
            self[expiry_key] = encode_time(time.time() + max_age - self.TIME_BASE)
        if add_nonce:
            self[nonce_key] = base64.urlsafe_b64encode(
                hashlib.sha256(os.urandom(1024)).digest())[
                    :int(math.ceil(nonce_bits / 6))]
        
        copy = self.copy()
        copy.discard(sig_key)
        copy.sort()
        self[sig_key] = copy._signature(key, hasher)

    def verify(self, key, hasher=None, max_age=None, time_key = TIME_KEY,
        sig_key=SIG_KEY, nonce_key=NONCE_KEY, expiry_key=EXPIRY_KEY, strict=False):

        # Make sure there is a sig.
        if sig_key not in self:
            return False

        # decode_time = int
        # decode_time = float
        # decode_time = self._decode_float
        decode_time = self._decode_int

        # Make sure it is good.
        copy = self.copy()
        del copy[sig_key]
        copy.sort()
        
        # We are comparing every character explicitly. This is so that all of
        # the failure cases take exactly the same amount of time. Don't try
        # to "clean" this up or you might introduce a timing attack.
        old_sig = self[sig_key]
        new_sig = copy._signature(key, hasher)
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
        if expiry_key in self:
            try:
                expiry_time = decode_time(self[expiry_key]) + self.TIME_BASE
            except struct.error:
                if strict:
                    raise ValueError('bad expiry time')
                return False
            if expiry_time < time.time():
                if strict:
                    raise ValueError('signature has expired')
                return False

        # Make sure it isnt too old.
        if max_age is not None and time_key in self:
            try:
                creation_time = decode_time(self[time_key]) + self.TIME_BASE
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
    import nose; nose.run(defaultTest=__name__)
