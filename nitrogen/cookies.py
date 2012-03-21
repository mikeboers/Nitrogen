
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


"""

import logging
import Cookie as stdlibcookies
import functools
import re
import string
import time
import hashlib

import werkzeug as wz
import werkzeug.utils

from . import sign


log = logging.getLogger(__name__)


CHARSET = 'utf-8'
ENCODE_ERRORS = 'strict'
DECODE_ERRORS = 'replace'


# The set of characters that do not require quoting according to RFC 2109 and
# RFC 2068.
SAFE_CHARS  = set(string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~")
# The set of characters that do not need ecaping iff we quote the string.
LEGAL_CHARS = SAFE_CHARS.union(set(' (),/;:<>=?@[]{}'))
LEGAL_CHARS = SAFE_CHARS.union(set(' (),/:<>=?@[]{}')) # Removed semicolon for FF 4.

_ATTRIBUTES = {
    "path": "Path",
    "comment": "Comment",
    "domain": "Domain",
    "max_age": "Max-Age",
    "secure": "secure",
    "version": "Version",
    "httponly": "HttpOnly",
    "http_only": "HttpOnly",
    "expires": "Expires",
}


def dump_cookie(name, value='', **kwargs):
    
    # Assert that the name is valid.
    if isinstance(name, unicode):
        try:
            name = name.encode('ascii')
        except UnicodeError:
            raise ValueError("illegal cookie name: %r." % name)
    if set(name).difference(SAFE_CHARS):
        raise ValueError("illegal cookie name: %r" % name)
    
    # Assert all args are valid.
    kwargs.setdefault('path', '/')
    for key in kwargs:
        if key not in _ATTRIBUTES:
            raise ValueError("unexpected keyword argument %r" % key)

    # Build the output.
    result = []
    result.append("%s=%s" % (name, _quote(value)))
    for key in sorted(_ATTRIBUTES):
        name = _ATTRIBUTES[key]
        value = kwargs.get(key)
        if value is not None:
            if key == "expires":
                result.append("%s=%s" % ('expires', wz.utils.cookie_date(value)))
            elif key == "max_age":
                result.append("%s=%d" % (name, value))
            elif key in ("secure", "httponly", "http_only") and value:
                result.append(name)
            else:
                result.append("%s=%s" % (name, value))
    return '; '.join(result)


_quote_map = {
    '\\': '\\\\',
    '"': '\\"'
}


def _quote_char(char):
    if char in LEGAL_CHARS:
        return char
    if char in _quote_map:
        return _quote_map[char]
    codepoint = ord(char)
    if codepoint < 256:
        return '\\x%02x' % codepoint
    if codepoint > 0xFFFF:
        return '\\U%08x' % codepoint
    return '\\u%04x' % codepoint


def _quote_byte(byte):
    if byte in LEGAL_CHARS:
        return byte
    if byte in _quote_map:
        return _quote_map[byte]
    return '\\%03o' % ord(byte)


def _quote(value):
    """Quote the given string so that it is safe for transport.
        
    This method uses a slightly more sophisticated quoting method than the
    RFC calls for, or the stdlib provides. We can encode unicode directly
    without resorting to utf-8 or the like.
        
    """
    if not set(value).difference(SAFE_CHARS):
        return str(value)
    if isinstance(value, unicode):
        return str('"' + ''.join(_quote_char(x) for x in value) + '"')
    return str('"' + ''.join(_quote_byte(x) for x in value) + '"')


_unquote_re = re.compile(r"\\(?:(x[0-9a-f]{2}|u[0-9a-f]{4}|U[0-9a-f]{8})|([0-3][0-7][0-7])|(.))", re.I)
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


def _unquote(value):
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
    return _unquote_re.sub(_unquote_cb, value)


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


def parse_cookies(input_string):
    """Load cookies from a string (presumably HTTP_COOKIE)."""
    
    cookies = {}
      
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
            break
        key, value = match.group("key"), match.group("val")
        i = match.end(0)
        # Parse the key, value in case it's metainfo
        if key[0] == "$":
            # We ignore attributes which pertain to the cookie
            # mechanism as a whole.  See RFC 2109.
            # (Does anyone care?)
            pass
        else:
            cookies[key] = _unquote(value)
    
    return cookies


class _RequestMixin(object):
        
    @wz.utils.cached_property
    def raw_cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        return self.dict_storage_class(parse_cookies(self.environ.get('HTTP_COOKIE', '')))
                                
    @wz.utils.cached_property
    def cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        raw = parse_cookies(self.environ.get('HTTP_COOKIE', ''))
        if not self.app.config.private_key:
            return self.dict_storage_class(raw)
        encryption_key = hashlib.md5(self.app.config.private_key).digest()    
        ret = {}
        for key, raw_value in raw.iteritems():
            try:
                ret[key] = sign.loads(encryption_key, raw_value, depends_on=dict(name=key), strict=True)
            except ValueError:
                pass
        return self.dict_storage_class(ret)


class _ResponseMixin(object):
    
    def set_raw_cookie(self, *args, **kwargs):
        self.headers.add('Set-Cookie', dump_cookie(*args, **kwargs))
    
    def set_cookie(self, *args, **kwargs):
        self.headers.add('Set-Cookie', self.app.dump_cookie(*args, **kwargs))


class CookieAppMixin(object):
    
    def dump_cookie(self, key, value='', max_age=None, **kwargs):
        if self.config.private_key:
            encryption_key = hashlib.md5(self.config.private_key).digest()
            value = sign.dumps(encryption_key, value, max_age=max_age, depends_on=dict(name=key))
        return dump_cookie(key, value, max_age=max_age, **kwargs)
        
    RequestMixin = _RequestMixin
    ResponseMixin = _ResponseMixin




