
# # coding: UTF-8
ur"""Mike's bastardization of the Python library Cookie module.

I found the Cookie module painfully inadequete, so I copied it here and started
tearing it apart.

The cookie RFCs are:
    RFC2068 - Hypertext Transfer Protocol
    RFC2109 - HTTP State Management Mechanism

TODO:
    - Determine how this all works with unicode.
    - Decide if we should default to path="/".
    - One function should build the headers Another function should build the
      headers that express the difference from another set of cookies. This is
      what build_cookies already does, and I believe that it should be made more
      explicit.
    - Use a different quoting function. Escape non-printables as \\xhh and UTF-8
      as \\uhhhh or \\Uhhhhhhhh. (Escaping here for doctest's sake.) May be able
      to simply use s.encode('unicode-escape') for the most part. The ast module
      may provide a function to load the returned stuff as a literal. Could also
      potentially use straight URL encoding.
        - The backslash might get destroyed by browsers. Do query encoding, but
          with a different symbol. "#" or "$"? Want to use a different symbol
          because it is likely I will store a query string in there. Make sure
          that all the base64 characters (or the URL safe ones) are okay. This
          allows the encrypted cookies to work out well as well.
    - None of the cookie metadata (max_age) should be accesable via item access.
      This will allow us to make a dict-cookie class which stores data in query
      form: "key=value" or "key:value|two:2" (if the second makes sense with encoding
      rules). This could even extend the uri.query.Query object and pick up the
      signing methods. Awesome.
    - Make sure that names can't start with '$' as per the spec.
    - Maybe seperate this all out into two classes. One which handles the
      parsing and one which handles the generating. Then a wrapper which binds
      them together into the class that we have now.
    - Consider implementing one of the various caching mechanisms in the RFC.
    - Add "expires" property to cookies that get/set a datetime based off of the
      max-age. We should only be outputting the "Max-Age", but we should except
      the "Expires" back.
    - Note that setting max-age to 0 only kills cookies if the path and domain
      precisely match (according to the spec). See if the path and such actually
      are being sent back to us...

NOTE on max_age
    max_age is None -> a session cookie
    max_age <=  0   -> expired

NOTE on all properties:
    If you just change the value of a cookie and not say anything about
    path/domain/expiry, the path/domain/expiry all get reset ANYWAYS.


Sending very basic cookies to the client:

    >>> cookies = Container()
    >>> cookies['key1'] = 'value1'
    >>> cookies['key2'] = 'value with spaces'
    >>> cookies.build_headers()
    [('Set-Cookie', 'key1=value1; Path=/'), ('Set-Cookie', 'key2="value with spaces"; Path=/')]

Cookie name must be only legal characters:
    
    >>> cookies['illegal name'] = "this wont show up."
    Traceback (most recent call last):
    ...
    ValueError: illegal key value: 'illegal name'

Expire some cookies:
    
    >>> cookies = Container('already1=value1')
    >>> cookies['key1'] = 'value1'
    >>> cookies['key2'] = 'value2'
    >>> cookies['key3'] = 'value3'
    >>> cookies['key2'].expire()
    >>> del cookies['key3']
    >>> del cookies['already1']
    >>> cookies
    <cookies.Container:{'key1': 'value1' 'key2': 'value2'}>
    
    >>> # Expiring headers will be sent.
    >>> cookies.build_headers()
    [('Set-Cookie', 'already1=; Max-Age=0; Path=/'), ('Set-Cookie', 'key1=value1; Path=/'), ('Set-Cookie', 'key2=; Max-Age=0; Path=/'), ('Set-Cookie', 'key3=; Max-Age=0; Path=/')]
    
    
Reading cookies:

    >>> cookies = Container('key=value; key_with_spaces="value with spaces"')
    >>> cookies['key']
    <Cookie: u'value'>
    >>> cookies['key'].value
    u'value'
    
    >>> cookies = Container('key=first; key=second')
    >>> cookies['key'].value
    u'first'
    >>> len(cookies)
    1
    >>> cookies.alllen()
    2
    >>> cookies.getall('key')
    [<Cookie: u'first'>, <Cookie: u'second'>]

Adding cookies to a container that started with HTTP_COOKIE cookies:
    
    >>> cookies['new'] = 'a new value'
    >>> cookies.build_headers()
    [('Set-Cookie', 'new="a new value"; Path=/')]
    >>> # Only the new cookie was output!

Set one with an expiry time:

    >>> cookies = Container()
    >>> cookies['expires'] = 'value that expires'
    >>> cookies['expires'].max_age = 10
    >>> cookies.build_headers()
    [('Set-Cookie', 'expires="value that expires"; Max-Age=10; Path=/')]

Set one that is more complex.
    >>> cookies = Container()
    >>> cookies.set('key', 'value',
    ...     domain='domain',
    ...     path='path',
    ...     max_age=60*60,
    ...     http_only=True,
    ...     secure=True
    ... )
    >>> cookies.build_headers()
    [('Set-Cookie', 'key=value; Domain=domain; HttpOnly; Max-Age=3600; Path=path; secure')]
    
More Unicode:
    >>> cookies = Container()
    >>> cookies[u'kéy'] = u'¡™£¢∞§¶•ªº' # doctest:+ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError: illegal key value: u'...'.
    >> cookies['unicode'] = u'¡™£¢∞§¶•ªº'
    >> cookies.build_headers()
    [('Set-Cookie', 'unicode="\\302\\241\\342\\204\\242\\302\\243\\302\\242\\342\\210\\236\\302\\247\\302\\266\\342\\200\\242\\302\\252\\302\\272"; Path=/')]
    
    >> cookies = Container('unicode="\\302\\241\\342\\204\\242\\302\\243\\302\\242\\342\\210\\236\\302\\247\\302\\266\\342\\200\\242\\302\\252\\302\\272"')
    >> repr(cookies['unicode'])
    "<Cookie: u'\\xa1\\u2122\\xa3\\xa2\\u221e\\xa7\\xb6\\u2022\\xaa\\xba'>"
    >> print cookies['unicode'].value
    ¡™£¢∞§¶•ªº
    
    >> cookies = Container()
    >> cookies['key'] = ''.join(unichr(x) for x in range(512))
    >> cookies.build_headers()
    [('Set-Cookie', 'key="\\000\\001\\002\\003\\004\\005\\006\\007\\010\\011\\012\\013\\014\\015\\016\\017\\020\\021\\022\\023\\024\\025\\026\\027\\030\\031\\032\\033\\034\\035\\036\\037 !\\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\177\\302\\200\\302\\201\\302\\202\\302\\203\\302\\204\\302\\205\\302\\206\\302\\207\\302\\210\\302\\211\\302\\212\\302\\213\\302\\214\\302\\215\\302\\216\\302\\217\\302\\220\\302\\221\\302\\222\\302\\223\\302\\224\\302\\225\\302\\226\\302\\227\\302\\230\\302\\231\\302\\232\\302\\233\\302\\234\\302\\235\\302\\236\\302\\237\\302\\240\\302\\241\\302\\242\\302\\243\\302\\244\\302\\245\\302\\246\\302\\247\\302\\250\\302\\251\\302\\252\\302\\253\\302\\254\\302\\255\\302\\256\\302\\257\\302\\260\\302\\261\\302\\262\\302\\263\\302\\264\\302\\265\\302\\266\\302\\267\\302\\270\\302\\271\\302\\272\\302\\273\\302\\274\\302\\275\\302\\276\\302\\277\\303\\200\\303\\201\\303\\202\\303\\203\\303\\204\\303\\205\\303\\206\\303\\207\\303\\210\\303\\211\\303\\212\\303\\213\\303\\214\\303\\215\\303\\216\\303\\217\\303\\220\\303\\221\\303\\222\\303\\223\\303\\224\\303\\225\\303\\226\\303\\227\\303\\230\\303\\231\\303\\232\\303\\233\\303\\234\\303\\235\\303\\236\\303\\237\\303\\240\\303\\241\\303\\242\\303\\243\\303\\244\\303\\245\\303\\246\\303\\247\\303\\250\\303\\251\\303\\252\\303\\253\\303\\254\\303\\255\\303\\256\\303\\257\\303\\260\\303\\261\\303\\262\\303\\263\\303\\264\\303\\265\\303\\266\\303\\267\\303\\270\\303\\271\\303\\272\\303\\273\\303\\274\\303\\275\\303\\276\\303\\277\\304\\200\\304\\201\\304\\202\\304\\203\\304\\204\\304\\205\\304\\206\\304\\207\\304\\210\\304\\211\\304\\212\\304\\213\\304\\214\\304\\215\\304\\216\\304\\217\\304\\220\\304\\221\\304\\222\\304\\223\\304\\224\\304\\225\\304\\226\\304\\227\\304\\230\\304\\231\\304\\232\\304\\233\\304\\234\\304\\235\\304\\236\\304\\237\\304\\240\\304\\241\\304\\242\\304\\243\\304\\244\\304\\245\\304\\246\\304\\247\\304\\250\\304\\251\\304\\252\\304\\253\\304\\254\\304\\255\\304\\256\\304\\257\\304\\260\\304\\261\\304\\262\\304\\263\\304\\264\\304\\265\\304\\266\\304\\267\\304\\270\\304\\271\\304\\272\\304\\273\\304\\274\\304\\275\\304\\276\\304\\277\\305\\200\\305\\201\\305\\202\\305\\203\\305\\204\\305\\205\\305\\206\\305\\207\\305\\210\\305\\211\\305\\212\\305\\213\\305\\214\\305\\215\\305\\216\\305\\217\\305\\220\\305\\221\\305\\222\\305\\223\\305\\224\\305\\225\\305\\226\\305\\227\\305\\230\\305\\231\\305\\232\\305\\233\\305\\234\\305\\235\\305\\236\\305\\237\\305\\240\\305\\241\\305\\242\\305\\243\\305\\244\\305\\245\\305\\246\\305\\247\\305\\250\\305\\251\\305\\252\\305\\253\\305\\254\\305\\255\\305\\256\\305\\257\\305\\260\\305\\261\\305\\262\\305\\263\\305\\264\\305\\265\\305\\266\\305\\267\\305\\270\\305\\271\\305\\272\\305\\273\\305\\274\\305\\275\\305\\276\\305\\277\\306\\200\\306\\201\\306\\202\\306\\203\\306\\204\\306\\205\\306\\206\\306\\207\\306\\210\\306\\211\\306\\212\\306\\213\\306\\214\\306\\215\\306\\216\\306\\217\\306\\220\\306\\221\\306\\222\\306\\223\\306\\224\\306\\225\\306\\226\\306\\227\\306\\230\\306\\231\\306\\232\\306\\233\\306\\234\\306\\235\\306\\236\\306\\237\\306\\240\\306\\241\\306\\242\\306\\243\\306\\244\\306\\245\\306\\246\\306\\247\\306\\250\\306\\251\\306\\252\\306\\253\\306\\254\\306\\255\\306\\256\\306\\257\\306\\260\\306\\261\\306\\262\\306\\263\\306\\264\\306\\265\\306\\266\\306\\267\\306\\270\\306\\271\\306\\272\\306\\273\\306\\274\\306\\275\\306\\276\\306\\277\\307\\200\\307\\201\\307\\202\\307\\203\\307\\204\\307\\205\\307\\206\\307\\207\\307\\210\\307\\211\\307\\212\\307\\213\\307\\214\\307\\215\\307\\216\\307\\217\\307\\220\\307\\221\\307\\222\\307\\223\\307\\224\\307\\225\\307\\226\\307\\227\\307\\230\\307\\231\\307\\232\\307\\233\\307\\234\\307\\235\\307\\236\\307\\237\\307\\240\\307\\241\\307\\242\\307\\243\\307\\244\\307\\245\\307\\246\\307\\247\\307\\250\\307\\251\\307\\252\\307\\253\\307\\254\\307\\255\\307\\256\\307\\257\\307\\260\\307\\261\\307\\262\\307\\263\\307\\264\\307\\265\\307\\266\\307\\267\\307\\270\\307\\271\\307\\272\\307\\273\\307\\274\\307\\275\\307\\276\\307\\277"; Path=/')]
    >> encoded = cookies.build_headers()[0][1]
    >> cookies = Container(encoded)
    >> repr(cookies['key'].value)
    'u\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0\\xa1\\xa2\\xa3\\xa4\\xa5\\xa6\\xa7\\xa8\\xa9\\xaa\\xab\\xac\\xad\\xae\\xaf\\xb0\\xb1\\xb2\\xb3\\xb4\\xb5\\xb6\\xb7\\xb8\\xb9\\xba\\xbb\\xbc\\xbd\\xbe\\xbf\\xc0\\xc1\\xc2\\xc3\\xc4\\xc5\\xc6\\xc7\\xc8\\xc9\\xca\\xcb\\xcc\\xcd\\xce\\xcf\\xd0\\xd1\\xd2\\xd3\\xd4\\xd5\\xd6\\xd7\\xd8\\xd9\\xda\\xdb\\xdc\\xdd\\xde\\xdf\\xe0\\xe1\\xe2\\xe3\\xe4\\xe5\\xe6\\xe7\\xe8\\xe9\\xea\\xeb\\xec\\xed\\xee\\xef\\xf0\\xf1\\xf2\\xf3\\xf4\\xf5\\xf6\\xf7\\xf8\\xf9\\xfa\\xfb\\xfc\\xfd\\xfe\\xff\\u0100\\u0101\\u0102\\u0103\\u0104\\u0105\\u0106\\u0107\\u0108\\u0109\\u010a\\u010b\\u010c\\u010d\\u010e\\u010f\\u0110\\u0111\\u0112\\u0113\\u0114\\u0115\\u0116\\u0117\\u0118\\u0119\\u011a\\u011b\\u011c\\u011d\\u011e\\u011f\\u0120\\u0121\\u0122\\u0123\\u0124\\u0125\\u0126\\u0127\\u0128\\u0129\\u012a\\u012b\\u012c\\u012d\\u012e\\u012f\\u0130\\u0131\\u0132\\u0133\\u0134\\u0135\\u0136\\u0137\\u0138\\u0139\\u013a\\u013b\\u013c\\u013d\\u013e\\u013f\\u0140\\u0141\\u0142\\u0143\\u0144\\u0145\\u0146\\u0147\\u0148\\u0149\\u014a\\u014b\\u014c\\u014d\\u014e\\u014f\\u0150\\u0151\\u0152\\u0153\\u0154\\u0155\\u0156\\u0157\\u0158\\u0159\\u015a\\u015b\\u015c\\u015d\\u015e\\u015f\\u0160\\u0161\\u0162\\u0163\\u0164\\u0165\\u0166\\u0167\\u0168\\u0169\\u016a\\u016b\\u016c\\u016d\\u016e\\u016f\\u0170\\u0171\\u0172\\u0173\\u0174\\u0175\\u0176\\u0177\\u0178\\u0179\\u017a\\u017b\\u017c\\u017d\\u017e\\u017f\\u0180\\u0181\\u0182\\u0183\\u0184\\u0185\\u0186\\u0187\\u0188\\u0189\\u018a\\u018b\\u018c\\u018d\\u018e\\u018f\\u0190\\u0191\\u0192\\u0193\\u0194\\u0195\\u0196\\u0197\\u0198\\u0199\\u019a\\u019b\\u019c\\u019d\\u019e\\u019f\\u01a0\\u01a1\\u01a2\\u01a3\\u01a4\\u01a5\\u01a6\\u01a7\\u01a8\\u01a9\\u01aa\\u01ab\\u01ac\\u01ad\\u01ae\\u01af\\u01b0\\u01b1\\u01b2\\u01b3\\u01b4\\u01b5\\u01b6\\u01b7\\u01b8\\u01b9\\u01ba\\u01bb\\u01bc\\u01bd\\u01be\\u01bf\\u01c0\\u01c1\\u01c2\\u01c3\\u01c4\\u01c5\\u01c6\\u01c7\\u01c8\\u01c9\\u01ca\\u01cb\\u01cc\\u01cd\\u01ce\\u01cf\\u01d0\\u01d1\\u01d2\\u01d3\\u01d4\\u01d5\\u01d6\\u01d7\\u01d8\\u01d9\\u01da\\u01db\\u01dc\\u01dd\\u01de\\u01df\\u01e0\\u01e1\\u01e2\\u01e3\\u01e4\\u01e5\\u01e6\\u01e7\\u01e8\\u01e9\\u01ea\\u01eb\\u01ec\\u01ed\\u01ee\\u01ef\\u01f0\\u01f1\\u01f2\\u01f3\\u01f4\\u01f5\\u01f6\\u01f7\\u01f8\\u01f9\\u01fa\\u01fb\\u01fc\\u01fd\\u01fe\\u01ff\''


Signed cookies:

    >>> SignedClass = make_signed_container('this is the key material')
    >>> signed = SignedClass()
    >>> signed['key'] = 'value'
    >>> encoded = signed.build_headers()[0][1]
    >>> encoded # doctest:+ELLIPSIS
    'key="_=value&_t=...&_n=...&_s=..."; Path=/'
    
    >>> verified = SignedClass(encoded)
    >>> verified['key'].value
    u'value'
    
    >>> encoded = encoded[:-10] + '"'
    >>> bad = SignedClass(encoded)
    >>> bad['key']
    Traceback (most recent call last):
    KeyError: 'key'
    
    >>> signed = SignedClass()
    >>> signed.set('key', 'this expires', max_age=10)
    >>> encoded = signed.build_headers()[0][1]
    >>> encoded # doctest:+ELLIPSIS
    'key="_=this+expires&_x=...&_n=...&_s=..."; Max-Age=10; Path=/'
    
    >>> verified = SignedClass(encoded)
    >>> verified['key'].value
    u'this expires'
    
    """


#
# Import our required modules
#
import collections
import Cookie as stdlibcookies
import cPickle as pickle
import functools
import logging
import re
import string
import time
import json

import werkzeug as wz

import multimap

# For signed cookies
from ..uri.query import Query

log = logging.getLogger(__name__)


CHARSET = 'utf-8'
ENCODE_ERRORS = 'strict'
DECODE_ERRORS = 'replace'

# The set of characters that do not require quoting according to RFC 2109 and
# RFC 2068.
SAFE_CHARS  = set(string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~")
# The set of characters that do not need ecaping iff we quote the string.
LEGAL_CHARS = SAFE_CHARS.union(set(' (),/;:<>=?@[]{}'))

            
_ATTRIBUTES = {
    "path": "Path",
    "comment": "Comment",
    "domain": "Domain",
    "max_age": "Max-Age",
    "secure": "secure",
    "version": "Version",
    "http_only": "HttpOnly",
}


class Cookie(object):
    # RFC 2109 lists these attributes as reserved:
    #   path    comment domain
    #   max-age secure  version
    #
    # This is an extension from Microsoft:
    #   http_only
    
    def __init__(self, value=None, **kwargs):
        """Create a new cookie.
        
        Kwargs set the various cookie attributes.
        
        """
        kwargs.setdefault('path', '/') 
        for key in kwargs:
            if key not in _ATTRIBUTES:
                raise ValueError("unexpected keyword argument %r" % k)
        self.value = value
        for key in _ATTRIBUTES:
            setattr(self, key, kwargs.get(key))
    
    def _as_tuple(self):
        """Get the current state of the cookie as a tuple.
        
        If the value is mutable, this will still be mutable.
        
        """
        ret = [('value', self.value)] + [(key, getattr(self, key)) for key in _ATTRIBUTES]
        return tuple((k, v) for k, v in ret if v is not None)
    
    def _set_change_checkpoint(self):
        """Set the reference for `Cookie.has_changed` to the current state.
        
        Includes values and attributes. This will be used to determine if the
        cookie has changes since it was recieved from the browser. If it has
        not changed, new headers will not be sent by default.
        
        """
        self._change_checkpoint = self._as_tuple()
    
    def has_changed(self):
        """Has this cookie changed since it was given to us by the browser?"""
        return self._as_tuple() != getattr(self, '_change_checkpoint', None)
    
    def expire(self):
        """Tell the browser to drop this cookie.
        
        Effectively sets max_age to 0. This does not remove the cookie from
        the container, and the cookie must not be removed if headers are to
        be sent to expire the cookie
        
        """
        self.max_age = 0
    
    @property
    def expired(self):
        """Dynamic property which indicates if the cookie has been expired."""
        return self.max_age is not None and self.max_age <= 0
    
    def __str__(self):
        """Returns the value of the cookie."""
        return self.value

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.value)
    
    

#
# Pattern for finding cookie
#
# This used to be strict parsing based on the RFC2109 and RFC2068
# specifications. I have since discovered that MSIE 3.0x doesn't
# follow the character rules outlined in those specs.  As a
# result, the parsing rules here are less strict.
#

_safe_charsPatt  = r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]"
_cookie_re = re.compile(
    r"(?x)"                       # This is a Verbose pattern
    r"(?P<key>"                   # Start of group 'key'
    ""+ _safe_charsPatt +"+?"    # Any word of at least one letter, nongreedy
    r")"                          # End of group 'key'
    r"\s*=\s*"                    # Equal Sign
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    r"|"                            # or
    ""+ _safe_charsPatt +"*"       # Any word or empty string
    r")"                          # End of group 'val'
    r"\s*;?"                      # Probably ending in a semi-colon
    )

class RawContainer(multimap.MutableMultiMap):
    
    cookie_class = Cookie
    
    def __init__(self, input=None, defaults=None, charset=None, encode_errors=None, decode_errors=None):
        multimap.MutableMultiMap.__init__(self)
        self.charset = charset
        self.defaults = defaults or {}
        self.encode_errors = encode_errors
        self.decode_errors = decode_errors
        if input:
            self.load(input)
    
    def blank_copy(self):
        return self.__class__(
            defaults=self.defaults.copy(),
            charset=self.charset,
            encode_errors=self.encode_errors,
            decode_errors=self.decode_errors
        )
            
    def load(self, input_string):
        """Load cookies from a string (presumably HTTP_COOKIE)."""
                    
        # This is from the original cookie module. I have elected not to
        # modify this much as of yet... Here be dragons!
        
        i = 0            # Our starting point
        length = len(input_string)     # Length of string
        cookie = None         # current morsel

        while 0 <= i < length:
            # Start looking for a cookie
            match = _cookie_re.search(input_string, i)
            if not match:
                # No more cookies
                return
            key, value = match.group("key"), match.group("val")
            i = match.end(0)
            # Parse the key, value in case it's metainfo
            if key[0] == "$":
                # We ignore attributes which pertain to the cookie
                # mechanism as a whole.  See RFC 2109.
                # (Does anyone care?)
                if cookie:
                    cookie[key[1:]] = value
            else:
                value = self._unquote(value)
                value = self._loads(key, value)
                if value is not None:
                    cookie = self.cookie_class(value)
                    cookie._set_change_checkpoint()
                    self.append((key, cookie))
    
    def _conform_key(self, key):
        # Make sure the key is legal.
        if isinstance(key, unicode):
            try:
                key = key.encode('ascii')
            except UnicodeError:
                raise ValueError("illegal key value: %r." % key)
        if set(key).difference(SAFE_CHARS):
            raise ValueError("illegal key value: %r" % key)
        return key
    
    def _conform_value(self, value):
        if isinstance(value, Cookie):
            return value
        cookie = self.cookie_class(**self.defaults)
        cookie.value = value
        return cookie
    
    def expire(self, key):
        """Expires a cookie."""
        if key not in self:
            self[key] = ''
        self[key].expire()
    
    def set(self, key, value, **kwargs):
        """Create a cookie with all attributes in one call."""
        attrs = self.defaults.copy()
        attrs.update(kwargs)
        self[key] = self.cookie_class(value, **attrs)
    
    _quote_map = {
        '\\': '\\\\',
        '"': '\\"'
    }
    
    @classmethod
    def _quote_char(cls, char):
        if char in LEGAL_CHARS:
            return char
        if char in cls._quote_map:
            return cls._quote_map[char]
        codepoint = ord(char)
        if codepoint < 256:
            return '\\x%02x' % codepoint
        if codepoint > 0xFFFF:
            return '\\U%08x' % codepoint
        return '\\u%04x' % codepoint
    
    @classmethod
    def _quote_byte(cls, byte):
        if byte in LEGAL_CHARS:
            return byte
        if char in cls._quote_map:
            return cls._quote_map[char]
        return '\\%03o' % ord(byte)
        
    @classmethod
    def _quote(cls, value):
        """Quote the given string so that it is safe for transport.
        
        This method uses a slightly more sophisticated quoting method than the
        RFC calls for, or the stdlib provides. We can encode unicode directly
        without resorting to utf-8 or the like.
        
        """
        if not set(value).difference(SAFE_CHARS):
            return str(value)
        if isinstance(value, unicode):
            return str('"' + ''.join(cls._quote_char(x) for x in value) + '"')
        return str('"' + ''.join(cls._quote_byte(x) for x in value) + '"')
    
    _unquote_re = re.compile(r"\\(?:(x[0-9a-f]{2}|u[0-9a-f]{4}|U[0-9a-f]{8})|([0-3][0-7][0-7])|(.))", re.I)
    @staticmethod
    def _unquote_cb(m):
        """Callback for unescaping characters in _unquote method.
        
        This one will return unicode characters if it uses any of the hex
        encodings (ie \\xXX, \\uXXXX, or \\UXXXXXXXX), and bytes for octal
        encodings. Hopefully then things which were encoded with this libary
        will automatically come out as unicode strings.
        
        """
        hex, octal, single = m.groups()
        if hex:
            return unichr(int(hex[1:], 16))
        if octal:
            return chr(int(octal, 8))
        return single
            
    @classmethod
    def _unquote(cls, value):
        """Remove transport encoding.
        
        This will process RFC quoted strings just fine, but also understands
        hex, and unicode escapes as well.
        
        This should return unicode strings if there was unicode at encoding
        time and it was prepared by this library. Otherwise they will be
        byte strings.
        
        """
        if not set(value).difference(SAFE_CHARS):
            return str(value)
        if value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        return cls._unquote_re.sub(cls._unquote_cb, value)
    
    
    def _dumps(self, name, value):
        """Serialize a cookie into a string.

        Overide this to provide more sophisticated encoding. Must return a
        string. Various _quote methods allow for unicode vs bytes.

        Defaults to just passing the string through; the _quote can handle
        unicode.

        """
        if not isinstance(value, basestring):
            return str(value)
        return value

    def _loads(self, name, raw_string):
        """Unserialize a cookie value.

        Overide to provide more sophisticated decoding. Can return any object.
        Raising a ValueError will have this cookie silently dropped.

        Defaults to UTF8 decoding the cookie, catching UnicodeErrors.

        """
        return raw_string
    
    def build_header(self, name, cookie, header="Set-Cookie"):
        """Build the header tuple for a given cookie."""
        result = []
        result.append("%s=%s" % (name, self._quote('' if cookie.expired else self._dumps(name, cookie))))
        for key in sorted(_ATTRIBUTES):
            name = _ATTRIBUTES[key]
            value = getattr(cookie, key)
            if value is not None:
                if key == "max_age":
                    result.append("%s=%d" % (name, value))
                    # result.append("%s=%s" % ('expires', wz.cookie_date(time.time() + value)))
                elif key in ("secure", "http_only") and value:
                    result.append(name)
                else:
                    result.append("%s=%s" % (name, value))
        return (header, '; '.join(result))

    def build_headers(self, all=False, header='Set-Cookie'):
        """Build a list of header tuples for all cookies in this container."""
        headers = []
        for name, cookie in self.iterallitems():
            if all or cookie.has_changed():
                headers.append(self.build_header(name, cookie, header=header))
        return headers

    def __repr__(self):
        L = []
        items = self.items()
        items.sort()
        for key, value in items:
            L.append('%r: %r' % (key, value.value))
        return '<%s.%s:{%s}>' % (self.__class__.__module__, self.__class__.__name__, ' '.join(L))


class Container(RawContainer):
    
    def _dumps(self, name, cookie):
        value = cookie.value
        if not isinstance(value, unicode):
            return str(value).decode(self.charset or CHARSET, self.encode_errors or ENCODE_ERRORS)
        return value
    
    def _loads(self, name, raw_string):    
        if isinstance(raw_string, unicode):
            return raw_string
        try:
            return raw_string.decode(self.charset or CHARSET, self.decode_errors or DECODE_ERRORS)
        except UnicodeDecodeError:
            pass




    
def make_encrypted_container(entropy):
    import crypto
    aes = crypto.AES(crypto.sha256(entropy).digest(), salt=True, base64=True)
    
    class EncryptedContainer(Container):
        class cookie_class(Cookie):
            @staticmethod
            def _dumps(name, cookie):
                value = cookie.value
                return aes.encrypt(pickle.dumps(value))
            @staticmethod
            def _loads(name, value):
                try:
                    return pickle.loads(aes.decrypt(value))
                except pickle.UnpicklingError:
                    pass
    
    return EncryptedContainer


class SignedContainer(Container):
    def __init__(self, *args, **kwargs):
        self.hmac_key = kwargs.pop('hmac_key')
        Container.__init__(self, *args, **kwargs)
    
    def blank_copy(self):
        return self.__class__(hmac_key=self.hmac_key)
    #     
    # def _quote(self, value):
    #     return '"%s"' % value
    # 
    # def _unquote(self, value):
    #     return value[1:-1]
    
    SIG_KEYS = dict(
        nonce_key='n',
        sig_key='s',
        time_key='t',
        expiry_key='x'
    )
    
    def _dumps(self, name, cookie):
        value = Container._dumps(self, name, cookie)
        query = Query(dict(name=name, value=value), charset=self.charset, encode_errors=self.encode_errors, decode_errors=self.decode_errors)
        query.sign(self.hmac_key, max_age=cookie.max_age, add_time=True, **self.SIG_KEYS)
        del query['value']
        del query['name']
        return value + ';' + str(query)

    def _loads(self, name, value):
        try:
            value, query = value.rsplit(';', 1)
        except ValueError:
            return
        query = Query(query, charset=self.charset, encode_errors=self.encode_errors, decode_errors=self.decode_errors)
        query['value'] = value
        query['name'] = name
        if query.verify(self.hmac_key, **self.SIG_KEYS):
            return value
    
    @classmethod
    def make_factory(cls, hmac_key):
        return functools.partial(cls, hmac_key=hmac_key)


class JsonContainer(SignedContainer):
    
    def _dumps(self, cookie):
        value = cookie.value
        return SignedContainer._dumps(self, json.dumps(value))
    
    def _loads(self, value):
        value = SignedContainer._loads(self, value)
        if value is not None:
            return json.loads(value)


make_signed_container = SignedContainer.make_factory



# This is the default environment key to use for caching the cookies and the
# default cookie factory. 
ENVIRON_KEY = 'nitrogen.req.cookies'


def get_factory(environ, hmac_key=None, factory=None, **kwargs):
    """Get the cookie container factory for the given environment and settings.
    
    A factory is a callable which takes a 'Cookie' HTTP header string and
    returns a cookie container.
    
    If provided 'factory', the given factory is returned immediately.
    Elif provided 'hmac_key', a SignedContainer factory is returned.
    Elif the factory was set with `setup_factory`, that is returned.
    Else, the base Container is returned.
    
    """
    environ_key = kwargs.get('environ_key', ENVIRON_KEY) + '.factory'
    factory = (
        factory or 
        (make_signed_container(hmac_key) if hmac_key else None) or
        environ.get(environ_key) or
        Container
    )
    return factory


def setup_factory(app, **kwargs):
    """WSGI middleware which sets the fallback cookie factory for this environ.
    
    Done as per the rules of `get_factory`.
    
    """
    def set_factory_app(environ, start):
        environ[kwargs.get('environ_key', ENVIRON_KEY) + '.factory'] = get_factory(environ, **kwargs)
        return app(environ, start)
    return set_factory_app
     
      
def parse_cookies(environ, **kwargs):
    """Return the cookies from the given environ.
    
    The cookies are only parsed the first time this is called, and the result
    is cached. Therefore, while the factory is settable via kwargs as per the
    rules of `get_factory`, they are only effective the first time. You must
    setup the cookies manually if you want something different on the second
    pass.
    
    """
    environ_key = kwargs.get('environ_key', ENVIRON_KEY)
    if environ_key not in environ:
        factory = get_factory(environ, **kwargs)
        environ[environ_key] = factory(environ.get('HTTP_COOKIE', ''))
    return environ[environ_key]



def test_quoting():
    import Cookie as cookielib
    
    
if __name__ == "__main__":
    import nose; nose.run(defaultTest=__name__)
    exit()
