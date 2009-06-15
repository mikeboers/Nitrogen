"""Mike's bastardization of the Python library Cookie module.

I found the Cookie module painfully inadequete, so I copied it here and stared
tearing it apart.

TODO:
    - determine how this all works with unicode

NOTE on maxage
    maxage is None -> Session cookie
    maxage <=  0 -> Expired

NOTE on all properties:
    If you just change the value of a cookie and not say anything about path/domain/expiry, the path/domain/expiry all get reset ANYWAYS.


Sending very basic cookies to the client:

    >>> cookies = Container()
    >>> cookies['key1'] = 'value1'
    >>> cookies['key2'] = 'value with spaces'
    >>> cookies.build_headers()
    [('Set-Cookie', 'key1=value1'), ('Set-Cookie', 'key2="value with spaces"')]

Cookie name must be only legal characters:
    
    >>> cookies['illegal name'] = "this wont show up."
    Traceback (most recent call last):
    ...
    Error: Illegal key value: illegal name

Expire some cookies:
    
    >>> cookies = Container('already1=value1')
    >>> cookies['key1'] = 'value1'
    >>> cookies['key2'] = 'value2'
    >>> cookies['key3'] = 'value3'
    >>> cookies['key2'].expire()
    >>> del cookies['key3']
    >>> del cookies['already1']
    >>> cookies
    <cookie.Container:{'key1': 'value1'}>
    
    >>> # Notice that you cannot access the expired cookies anymore.
    >>> cookies['key2']
    Traceback (most recent call last):
    ...
    KeyError: 'key2'
    
    >>> # Expiring headers will still be sent.
    >>> cookies.build_headers()
    [('Set-Cookie', 'already1=; Max-Age=0'), ('Set-Cookie', 'key1=value1'), ('Set-Cookie', 'key2=; Max-Age=0'), ('Set-Cookie', 'key3=; Max-Age=0')]
    
    
Reading cookies:

    >>> cookies = Container('key=value; key_with_spaces="value with spaces"')
    >>> cookies['key']
    <Cookie: 'value'>
    >>> cookies['key'].value
    'value'

Adding cookies to a container that started with HTTP_COOKIE cookies:
    
    >>> cookies['new'] = 'a new value'
    >>> cookies.build_headers()
    [('Set-Cookie', 'new="a new value"')]
    >>> # Only the new cookie was output!

Set one with an expiry time:

    >>> cookies = Container()
    >>> cookies['expires'] = 'value that expires'
    >>> cookies['expires'].maxage = 10
    >>> cookies.build_headers()
    [('Set-Cookie', 'expires="value that expires"; Max-Age=10')]

Set one that is more complex.
    >>> cookies = Container()
    >>> cookies.create('key', 'value',
    ...     domain='domain',
    ...     path='path',
    ...     maxage=60*60,
    ...     httponly=True,
    ...     secure=True
    ... )
    >>> cookies.build_headers()
    [('Set-Cookie', 'key=value; Domain=domain; httponly; Max-Age=3600; Path=path; secure')]
    

"""

#
# Import our required modules
#
import string
import collections
import re

# These are for the encrypted cookies.
try:
    import cPickle as pickle
except ImportError:
    import pickle

# For signed cookies
try:
    from ..uri.query import Query
except ValueError:
    # For local testing.
    import sys
    sys.path.append('..')
    from uri.query import Query


# Define an exception visible to External modules
class Error(Exception):
    pass


# These quoting routines conform to the RFC2109 specification, which in
# turn references the character definitions from RFC2068. They provide
# a two-way quoting algorithm. Any non-text character is translated
# into a 4 character sequence: a forward-slash followed by the
# three-digit octal equivalent of the character.  Any '\' or '"' is
# quoted with a preceeding '\' slash.
#
# These are taken from RFC2068 and RFC2109.
#       _legal_chars       is the list of chars which don't require "'s
#       _encoding_map       hash-table for fast quoting
#
_legal_chars = string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~"

_encoding_map = {
    '\000' : '\\000',  '\001' : '\\001',  '\002' : '\\002',
    '\003' : '\\003',  '\004' : '\\004',  '\005' : '\\005',
    '\006' : '\\006',  '\007' : '\\007',  '\010' : '\\010',
    '\011' : '\\011',  '\012' : '\\012',  '\013' : '\\013',
    '\014' : '\\014',  '\015' : '\\015',  '\016' : '\\016',
    '\017' : '\\017',  '\020' : '\\020',  '\021' : '\\021',
    '\022' : '\\022',  '\023' : '\\023',  '\024' : '\\024',
    '\025' : '\\025',  '\026' : '\\026',  '\027' : '\\027',
    '\030' : '\\030',  '\031' : '\\031',  '\032' : '\\032',
    '\033' : '\\033',  '\034' : '\\034',  '\035' : '\\035',
    '\036' : '\\036',  '\037' : '\\037',
    
    '"' : '\\"',       '\\' : '\\\\',
    
    '\177' : '\\177',  '\200' : '\\200',  '\201' : '\\201',
    '\202' : '\\202',  '\203' : '\\203',  '\204' : '\\204',
    '\205' : '\\205',  '\206' : '\\206',  '\207' : '\\207',
    '\210' : '\\210',  '\211' : '\\211',  '\212' : '\\212',
    '\213' : '\\213',  '\214' : '\\214',  '\215' : '\\215',
    '\216' : '\\216',  '\217' : '\\217',  '\220' : '\\220',
    '\221' : '\\221',  '\222' : '\\222',  '\223' : '\\223',
    '\224' : '\\224',  '\225' : '\\225',  '\226' : '\\226',
    '\227' : '\\227',  '\230' : '\\230',  '\231' : '\\231',
    '\232' : '\\232',  '\233' : '\\233',  '\234' : '\\234',
    '\235' : '\\235',  '\236' : '\\236',  '\237' : '\\237',
    '\240' : '\\240',  '\241' : '\\241',  '\242' : '\\242',
    '\243' : '\\243',  '\244' : '\\244',  '\245' : '\\245',
    '\246' : '\\246',  '\247' : '\\247',  '\250' : '\\250',
    '\251' : '\\251',  '\252' : '\\252',  '\253' : '\\253',
    '\254' : '\\254',  '\255' : '\\255',  '\256' : '\\256',
    '\257' : '\\257',  '\260' : '\\260',  '\261' : '\\261',
    '\262' : '\\262',  '\263' : '\\263',  '\264' : '\\264',
    '\265' : '\\265',  '\266' : '\\266',  '\267' : '\\267',
    '\270' : '\\270',  '\271' : '\\271',  '\272' : '\\272',
    '\273' : '\\273',  '\274' : '\\274',  '\275' : '\\275',
    '\276' : '\\276',  '\277' : '\\277',  '\300' : '\\300',
    '\301' : '\\301',  '\302' : '\\302',  '\303' : '\\303',
    '\304' : '\\304',  '\305' : '\\305',  '\306' : '\\306',
    '\307' : '\\307',  '\310' : '\\310',  '\311' : '\\311',
    '\312' : '\\312',  '\313' : '\\313',  '\314' : '\\314',
    '\315' : '\\315',  '\316' : '\\316',  '\317' : '\\317',
    '\320' : '\\320',  '\321' : '\\321',  '\322' : '\\322',
    '\323' : '\\323',  '\324' : '\\324',  '\325' : '\\325',
    '\326' : '\\326',  '\327' : '\\327',  '\330' : '\\330',
    '\331' : '\\331',  '\332' : '\\332',  '\333' : '\\333',
    '\334' : '\\334',  '\335' : '\\335',  '\336' : '\\336',
    '\337' : '\\337',  '\340' : '\\340',  '\341' : '\\341',
    '\342' : '\\342',  '\343' : '\\343',  '\344' : '\\344',
    '\345' : '\\345',  '\346' : '\\346',  '\347' : '\\347',
    '\350' : '\\350',  '\351' : '\\351',  '\352' : '\\352',
    '\353' : '\\353',  '\354' : '\\354',  '\355' : '\\355',
    '\356' : '\\356',  '\357' : '\\357',  '\360' : '\\360',
    '\361' : '\\361',  '\362' : '\\362',  '\363' : '\\363',
    '\364' : '\\364',  '\365' : '\\365',  '\366' : '\\366',
    '\367' : '\\367',  '\370' : '\\370',  '\371' : '\\371',
    '\372' : '\\372',  '\373' : '\\373',  '\374' : '\\374',
    '\375' : '\\375',  '\376' : '\\376',  '\377' : '\\377'
    }

_idmap = ''.join(chr(x) for x in xrange(256))
        
def _quote(to_quote):
    #
    # If the string does not need to be double-quoted,
    # then just return the string.  Otherwise, surround
    # the string in doublequotes and precede quote (with a \)
    # special characters.
    #
    if not to_quote.translate(_idmap, _legal_chars):
        return to_quote
    else:
        return '"' + ''.join(map(_encoding_map.get, to_quote, to_quote)) + '"'
# end _quote

_octal_re = re.compile(r"\\[0-3][0-7][0-7]")
_quote_re = re.compile(r"[\\].")

def _unquote(to_unquote):    
    # If there aren't any doublequotes,
    # then there can't be any special characters.  See RFC 2109.
    if len(to_unquote) < 2:
        return to_unquote
    if to_unquote[0] != '"' or to_unquote[-1] != '"':
        return to_unquote

    # We have to assume that we must decode this string.
    # Down to work.

    # Remove the "s
    to_unquote = to_unquote[1:-1]

    # Check for special sequences.  Examples:
    #    \012 --> \n
    #    \"   --> "
    #
    i = 0
    n = len(to_unquote)
    res = []
    while 0 <= i < n:
        octal_match = _octal_re.search(to_unquote, i)
        quote_match = _quote_re.search(to_unquote, i)
        if not octal_match and not quote_match: # Neither matched.
            res.append(to_unquote[i:])
            break
        # else:
        j = k = -1
        if octal_match: j = octal_match.start(0)
        if quote_match: k = quote_match.start(0)
        if quote_match and (not octal_match or k < j): # QuotePatt matched first.
            res.append(to_unquote[i:k])
            res.append(to_unquote[k+1])
            i = k+2
        else: # OctalPatt matched first.
            res.append(to_unquote[i:j])
            res.append(chr(int(to_unquote[j+1:j+4], 8)))
            i = j+4
    
    return ''.join(res)


_attr_map = {
    "path" : "Path",
    "comment" : "Comment",
    "domain" : "Domain",
    "maxage" : "Max-Age",
    "secure" : "secure",
    "httponly" : "httponly",
    "version" : "Version",
}

class Cookie(object):
    # RFC 2109 lists these attributes as reserved:
    #   path    comment domain
    #   max-age secure  version
    #
    # This is an extension from Microsoft:
    #   httponly
    
    # This dictionary provides a mapping from the lowercase
    # variant on the left to the appropriate traditional
    # formatting on the right.
    
    def __init__(self, value=None, **kwargs):
        
        for key in kwargs:
            if key not in _attr_map:
                raise TypeError("__init__() got an unexpected keyword argument %r" % k)
        
        self._init_value = None
        
        self.value = value
        for key in _attr_map:
            setattr(self, key, kwargs.get(key))
        
    
    @classmethod
    def rebuild(cls, encoded_value):
        cookie = cls()
        cookie.value = cookie._loads(encoded_value)
        cookie._init_value = cookie._tuple()
        return cookie
    
    def _tuple(self):
        ret = (('value', self.value), )
        ret += tuple((key, getattr(self, key)) for key in _attr_map)
        ret = tuple((k, v) for k, v in ret if v is not None)
        return ret    
    
    def has_changed(self):
        return self._tuple() != self._init_value
    
    def expire(self):
        """Tell the browser to drop this cookie.
        
        Effectively sets maxage to 0.
        """
        
        self.maxage = 0
    
    def is_expired(self):
        return self.maxage is not None and self.maxage <= 0
    
    def __str__(self):
        """Returns the value of the cookie."""
        return self.value

    def __repr__(self):
        return '<%s: %r>' % (self.__class__.__name__, self.value)
    
    def build_header(self, key, header="Set-Cookie"):
        # Build up our result
        result = []
        
        # First, the key=value pair
        result.append("%s=%s" % (key, _quote('' if self.is_expired() else self._dumps(self.value))))

        # Now add any defined attributes
        for key in sorted(_attr_map):
            name = _attr_map[key]
            value = getattr(self, key)
            if value is not None:
                if key == "max-age":
                    result.append("%s=%d" % (name, value))
                elif key == "secure" and value:
                    result.append(name)
                elif key == "httponly" and value:
                    result.append(name)
                else:
                    result.append("%s=%s" % (name, value))

        # Return the result
        return (header, '; '.join(result))
    
    @staticmethod
    def _loads(raw_string):
        """Overide me to provide more sophisticated decoding."""
        return raw_string
    
    @staticmethod
    def _dumps(value):
        """Overide me to provide more sophisticated encoding."""
        return str(value)

#
# Pattern for finding cookie
#
# This used to be strict parsing based on the RFC2109 and RFC2068
# specifications. I have since discovered that MSIE 3.0x doesn't
# follow the character rules outlined in those specs.  As a
# result, the parsing rules here are less strict.
#

_legal_charsPatt  = r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]"
_cookie_re = re.compile(
    r"(?x)"                       # This is a Verbose pattern
    r"(?P<key>"                   # Start of group 'key'
    ""+ _legal_charsPatt +"+?"    # Any word of at least one letter, nongreedy
    r")"                          # End of group 'key'
    r"\s*=\s*"                    # Equal Sign
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    r"|"                            # or
    ""+ _legal_charsPatt +"*"       # Any word or empty string
    r")"                          # End of group 'val'
    r"\s*;?"                      # Probably ending in a semi-colon
    )

class Container(collections.MutableMapping):
    
    cookie_class = Cookie
    
    def __init__(self, input=None):
        self._cookies = {}
        if input:
            self.load(input)
            
    def load(self, raw_data):
        """Load cookies from a string (presumably HTTP_COOKIE)."""
        self._parse_string(raw_data)
            
    def __setitem__(self, key, value):
        """Create a cookie with only a value."""
        
        # Set a Cookie object if given.
        if isinstance(value, Cookie):
            self._cookies[key] = value
        else:
            # Make sure the key is legal.
            if "" != key.translate(_idmap, _legal_chars):
                raise Error("Illegal key value: %s" % key)
            # Build (if nessesary) and set the cookie.
            cookie = self.get(key, self.cookie_class())
            cookie.value = value
            self._cookies[key] = cookie
    
    def __getitem__(self, key):
        """Normal dict access, but ignores expired cookies."""
        c = self._cookies[key]
        if c.is_expired():
            raise KeyError(key)
        return c
    
    def __contains__(self, key):
        return key in self._cookies
    
    def __iter__(self):
        """Normal dict iterator, but ignores expired cookies."""
        for k, v in self._cookies.iteritems():
            if not v.is_expired():
                yield k
    
    def __len__(self):
        """Number of non-expired cookies."""
        return len(list(self.__iter__()))
    
    def __delitem__(self, key):
        """Expires a cookie (effectively removing it from the dict)."""
        self._cookies[key].expire()
    
    def create(self, key, value, **kwargs):
        """Create a cookie with all attributes in one call."""
        self._cookies[key] = self.cookie_class(value, **kwargs)
    
    def build_headers(self, all=False, header='Set-Cookie'):
        """Build a list of header tuples suitable to pass to WSGI start callback."""
        headers = []
        for key, cookie in sorted(self._cookies.items()):
            if all or cookie.has_changed():
                headers.append(cookie.build_header(key, header=header))
        return headers

    def __repr__(self):
        L = []
        items = self.items()
        items.sort()
        for key, value in items:
            L.append('%r: %r' % (key, value.value))
        return '<cookie.Container:{%s}>' % ' '.join(L)

    def _parse_string(self, input_string):
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
                try:
                    cookie = self[key] = self.cookie_class.rebuild(_unquote(value))
                except Error:
                    pass


def make_encrypted_container(entropy):
    import crypto
    aes = crypto.AES(crypto.sha256(entropy).digest(), salt=True, base64=True)
    
    class EncryptedContainer(Container):
        class cookie_class(Cookie):
            @staticmethod
            def _dumps(value):
                return aes.encrypt(pickle.dumps(value))
            @staticmethod
            def _loads(value):
                try:
                    return pickle.loads(aes.decrypt(value))
                except Exception, e:
                    raise Error('Bad pickle.')
    
    return EncryptedContainer

def make_signed_container(entropy, maxage=None):
    """Builds a signed cookie container class.
    
    Examples:
    
        >>> SignedClass = make_signed_container('this is the key material')
        >>> signed = SignedClass()
        >>> signed['key'] = 'value'
        >>> encoded = signed.build_headers()[0][1]
        >>> encoded # doctest:+ELLIPSIS
        'key="v=value&n=...&s=..."'
        
        >>> verified = SignedClass(encoded)
        >>> verified['key'].value
        'value'
        
        >>> encoded = encoded[:-5] + '"'
        >>> bad = SignedClass(encoded)
        >>> bad['key']
        Traceback (most recent call last):
        KeyError: 'key'
        
        >>> signed = SignedClass()
        >>> signed.create('key', 'this expires', maxage=10)
        >>> encoded = signed.build_headers()[0][1]
        >>> encoded # doctest:+ELLIPSIS
        'key="v=this%20expires&x=...&n=...&s=..."; Max-Age=10'
        
        >>> verified = SignedClass(encoded)
        >>> verified['key'].value
        'this expires'
        
    """
    
    import os
    import hmac
    import hashlib
    import time
    
    class SignedContainer(Container):
        class cookie_class(Cookie):
            
            def _dumps(self, value):
                query = Query()
                query['v'] = value
                maxages = [x for x in [self.maxage, maxage] if x is not None]
                if maxages:
                    query['x'] = int(time.time()) + min(maxages)
                query['n'] = os.urandom(4).encode('hex')
                query['s'] = hmac.new(entropy, str(query), hashlib.md5).hexdigest()
                return str(query)
            
            @staticmethod
            def _loads(value):
                try:
                    query = Query(value)
                    sig = query['s']
                    del query['s']
                    if hmac.new(entropy, str(query), hashlib.md5).hexdigest() != sig:
                        raise Error("Bad signature.")
                    if 'x' in query and int(query['x']) < time.time():
                        raise Error("Expired cookie.")
                    return query['v']
                except Exception as e:
                    raise Error(str(e))

    return SignedContainer

if __name__ == "__main__":
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."



