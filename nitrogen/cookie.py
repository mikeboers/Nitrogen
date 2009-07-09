# coding: UTF-8
ur"""Mike's bastardization of the Python library Cookie module.

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
    Error: Illegal key value: 'illegal name'

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
    <Cookie: u'value'>
    >>> cookies['key'].value
    u'value'

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
    
More Unicode:
    >>> cookies = Container()
    >>> cookies[u'kéy'] = u'¡™£¢∞§¶•ªº' # doctest:+ELLIPSIS
    Traceback (most recent call last):
    ...
    Error: Illegal key value: u'...'.
    >>> cookies['unicode'] = u'¡™£¢∞§¶•ªº'
    >>> cookies.build_headers()
    [('Set-Cookie', 'unicode="\\302\\241\\342\\204\\242\\302\\243\\302\\242\\342\\210\\236\\302\\247\\302\\266\\342\\200\\242\\302\\252\\302\\272"')]
    
    >>> cookies = Container('unicode="\\302\\241\\342\\204\\242\\302\\243\\302\\242\\342\\210\\236\\302\\247\\302\\266\\342\\200\\242\\302\\252\\302\\272"')
    >>> repr(cookies['unicode'])
    "<Cookie: u'\\xa1\\u2122\\xa3\\xa2\\u221e\\xa7\\xb6\\u2022\\xaa\\xba'>"
    >>> print cookies['unicode'].value
    ¡™£¢∞§¶•ªº
    
    >>> cookies = Container()
    >>> cookies['key'] = ''.join(unichr(x) for x in range(512))
    >>> cookies.build_headers()
    [('Set-Cookie', 'key="\\000\\001\\002\\003\\004\\005\\006\\007\\010\\011\\012\\013\\014\\015\\016\\017\\020\\021\\022\\023\\024\\025\\026\\027\\030\\031\\032\\033\\034\\035\\036\\037 !\\"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\177\\302\\200\\302\\201\\302\\202\\302\\203\\302\\204\\302\\205\\302\\206\\302\\207\\302\\210\\302\\211\\302\\212\\302\\213\\302\\214\\302\\215\\302\\216\\302\\217\\302\\220\\302\\221\\302\\222\\302\\223\\302\\224\\302\\225\\302\\226\\302\\227\\302\\230\\302\\231\\302\\232\\302\\233\\302\\234\\302\\235\\302\\236\\302\\237\\302\\240\\302\\241\\302\\242\\302\\243\\302\\244\\302\\245\\302\\246\\302\\247\\302\\250\\302\\251\\302\\252\\302\\253\\302\\254\\302\\255\\302\\256\\302\\257\\302\\260\\302\\261\\302\\262\\302\\263\\302\\264\\302\\265\\302\\266\\302\\267\\302\\270\\302\\271\\302\\272\\302\\273\\302\\274\\302\\275\\302\\276\\302\\277\\303\\200\\303\\201\\303\\202\\303\\203\\303\\204\\303\\205\\303\\206\\303\\207\\303\\210\\303\\211\\303\\212\\303\\213\\303\\214\\303\\215\\303\\216\\303\\217\\303\\220\\303\\221\\303\\222\\303\\223\\303\\224\\303\\225\\303\\226\\303\\227\\303\\230\\303\\231\\303\\232\\303\\233\\303\\234\\303\\235\\303\\236\\303\\237\\303\\240\\303\\241\\303\\242\\303\\243\\303\\244\\303\\245\\303\\246\\303\\247\\303\\250\\303\\251\\303\\252\\303\\253\\303\\254\\303\\255\\303\\256\\303\\257\\303\\260\\303\\261\\303\\262\\303\\263\\303\\264\\303\\265\\303\\266\\303\\267\\303\\270\\303\\271\\303\\272\\303\\273\\303\\274\\303\\275\\303\\276\\303\\277\\304\\200\\304\\201\\304\\202\\304\\203\\304\\204\\304\\205\\304\\206\\304\\207\\304\\210\\304\\211\\304\\212\\304\\213\\304\\214\\304\\215\\304\\216\\304\\217\\304\\220\\304\\221\\304\\222\\304\\223\\304\\224\\304\\225\\304\\226\\304\\227\\304\\230\\304\\231\\304\\232\\304\\233\\304\\234\\304\\235\\304\\236\\304\\237\\304\\240\\304\\241\\304\\242\\304\\243\\304\\244\\304\\245\\304\\246\\304\\247\\304\\250\\304\\251\\304\\252\\304\\253\\304\\254\\304\\255\\304\\256\\304\\257\\304\\260\\304\\261\\304\\262\\304\\263\\304\\264\\304\\265\\304\\266\\304\\267\\304\\270\\304\\271\\304\\272\\304\\273\\304\\274\\304\\275\\304\\276\\304\\277\\305\\200\\305\\201\\305\\202\\305\\203\\305\\204\\305\\205\\305\\206\\305\\207\\305\\210\\305\\211\\305\\212\\305\\213\\305\\214\\305\\215\\305\\216\\305\\217\\305\\220\\305\\221\\305\\222\\305\\223\\305\\224\\305\\225\\305\\226\\305\\227\\305\\230\\305\\231\\305\\232\\305\\233\\305\\234\\305\\235\\305\\236\\305\\237\\305\\240\\305\\241\\305\\242\\305\\243\\305\\244\\305\\245\\305\\246\\305\\247\\305\\250\\305\\251\\305\\252\\305\\253\\305\\254\\305\\255\\305\\256\\305\\257\\305\\260\\305\\261\\305\\262\\305\\263\\305\\264\\305\\265\\305\\266\\305\\267\\305\\270\\305\\271\\305\\272\\305\\273\\305\\274\\305\\275\\305\\276\\305\\277\\306\\200\\306\\201\\306\\202\\306\\203\\306\\204\\306\\205\\306\\206\\306\\207\\306\\210\\306\\211\\306\\212\\306\\213\\306\\214\\306\\215\\306\\216\\306\\217\\306\\220\\306\\221\\306\\222\\306\\223\\306\\224\\306\\225\\306\\226\\306\\227\\306\\230\\306\\231\\306\\232\\306\\233\\306\\234\\306\\235\\306\\236\\306\\237\\306\\240\\306\\241\\306\\242\\306\\243\\306\\244\\306\\245\\306\\246\\306\\247\\306\\250\\306\\251\\306\\252\\306\\253\\306\\254\\306\\255\\306\\256\\306\\257\\306\\260\\306\\261\\306\\262\\306\\263\\306\\264\\306\\265\\306\\266\\306\\267\\306\\270\\306\\271\\306\\272\\306\\273\\306\\274\\306\\275\\306\\276\\306\\277\\307\\200\\307\\201\\307\\202\\307\\203\\307\\204\\307\\205\\307\\206\\307\\207\\307\\210\\307\\211\\307\\212\\307\\213\\307\\214\\307\\215\\307\\216\\307\\217\\307\\220\\307\\221\\307\\222\\307\\223\\307\\224\\307\\225\\307\\226\\307\\227\\307\\230\\307\\231\\307\\232\\307\\233\\307\\234\\307\\235\\307\\236\\307\\237\\307\\240\\307\\241\\307\\242\\307\\243\\307\\244\\307\\245\\307\\246\\307\\247\\307\\250\\307\\251\\307\\252\\307\\253\\307\\254\\307\\255\\307\\256\\307\\257\\307\\260\\307\\261\\307\\262\\307\\263\\307\\264\\307\\265\\307\\266\\307\\267\\307\\270\\307\\271\\307\\272\\307\\273\\307\\274\\307\\275\\307\\276\\307\\277"')]
    >>> encoded = cookies.build_headers()[0][1]
    >>> cookies = Container(encoded)
    >>> repr(cookies['key'].value)
    'u\'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f\\x10\\x11\\x12\\x13\\x14\\x15\\x16\\x17\\x18\\x19\\x1a\\x1b\\x1c\\x1d\\x1e\\x1f !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\\x7f\\x80\\x81\\x82\\x83\\x84\\x85\\x86\\x87\\x88\\x89\\x8a\\x8b\\x8c\\x8d\\x8e\\x8f\\x90\\x91\\x92\\x93\\x94\\x95\\x96\\x97\\x98\\x99\\x9a\\x9b\\x9c\\x9d\\x9e\\x9f\\xa0\\xa1\\xa2\\xa3\\xa4\\xa5\\xa6\\xa7\\xa8\\xa9\\xaa\\xab\\xac\\xad\\xae\\xaf\\xb0\\xb1\\xb2\\xb3\\xb4\\xb5\\xb6\\xb7\\xb8\\xb9\\xba\\xbb\\xbc\\xbd\\xbe\\xbf\\xc0\\xc1\\xc2\\xc3\\xc4\\xc5\\xc6\\xc7\\xc8\\xc9\\xca\\xcb\\xcc\\xcd\\xce\\xcf\\xd0\\xd1\\xd2\\xd3\\xd4\\xd5\\xd6\\xd7\\xd8\\xd9\\xda\\xdb\\xdc\\xdd\\xde\\xdf\\xe0\\xe1\\xe2\\xe3\\xe4\\xe5\\xe6\\xe7\\xe8\\xe9\\xea\\xeb\\xec\\xed\\xee\\xef\\xf0\\xf1\\xf2\\xf3\\xf4\\xf5\\xf6\\xf7\\xf8\\xf9\\xfa\\xfb\\xfc\\xfd\\xfe\\xff\\u0100\\u0101\\u0102\\u0103\\u0104\\u0105\\u0106\\u0107\\u0108\\u0109\\u010a\\u010b\\u010c\\u010d\\u010e\\u010f\\u0110\\u0111\\u0112\\u0113\\u0114\\u0115\\u0116\\u0117\\u0118\\u0119\\u011a\\u011b\\u011c\\u011d\\u011e\\u011f\\u0120\\u0121\\u0122\\u0123\\u0124\\u0125\\u0126\\u0127\\u0128\\u0129\\u012a\\u012b\\u012c\\u012d\\u012e\\u012f\\u0130\\u0131\\u0132\\u0133\\u0134\\u0135\\u0136\\u0137\\u0138\\u0139\\u013a\\u013b\\u013c\\u013d\\u013e\\u013f\\u0140\\u0141\\u0142\\u0143\\u0144\\u0145\\u0146\\u0147\\u0148\\u0149\\u014a\\u014b\\u014c\\u014d\\u014e\\u014f\\u0150\\u0151\\u0152\\u0153\\u0154\\u0155\\u0156\\u0157\\u0158\\u0159\\u015a\\u015b\\u015c\\u015d\\u015e\\u015f\\u0160\\u0161\\u0162\\u0163\\u0164\\u0165\\u0166\\u0167\\u0168\\u0169\\u016a\\u016b\\u016c\\u016d\\u016e\\u016f\\u0170\\u0171\\u0172\\u0173\\u0174\\u0175\\u0176\\u0177\\u0178\\u0179\\u017a\\u017b\\u017c\\u017d\\u017e\\u017f\\u0180\\u0181\\u0182\\u0183\\u0184\\u0185\\u0186\\u0187\\u0188\\u0189\\u018a\\u018b\\u018c\\u018d\\u018e\\u018f\\u0190\\u0191\\u0192\\u0193\\u0194\\u0195\\u0196\\u0197\\u0198\\u0199\\u019a\\u019b\\u019c\\u019d\\u019e\\u019f\\u01a0\\u01a1\\u01a2\\u01a3\\u01a4\\u01a5\\u01a6\\u01a7\\u01a8\\u01a9\\u01aa\\u01ab\\u01ac\\u01ad\\u01ae\\u01af\\u01b0\\u01b1\\u01b2\\u01b3\\u01b4\\u01b5\\u01b6\\u01b7\\u01b8\\u01b9\\u01ba\\u01bb\\u01bc\\u01bd\\u01be\\u01bf\\u01c0\\u01c1\\u01c2\\u01c3\\u01c4\\u01c5\\u01c6\\u01c7\\u01c8\\u01c9\\u01ca\\u01cb\\u01cc\\u01cd\\u01ce\\u01cf\\u01d0\\u01d1\\u01d2\\u01d3\\u01d4\\u01d5\\u01d6\\u01d7\\u01d8\\u01d9\\u01da\\u01db\\u01dc\\u01dd\\u01de\\u01df\\u01e0\\u01e1\\u01e2\\u01e3\\u01e4\\u01e5\\u01e6\\u01e7\\u01e8\\u01e9\\u01ea\\u01eb\\u01ec\\u01ed\\u01ee\\u01ef\\u01f0\\u01f1\\u01f2\\u01f3\\u01f4\\u01f5\\u01f6\\u01f7\\u01f8\\u01f9\\u01fa\\u01fb\\u01fc\\u01fd\\u01fe\\u01ff\''
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

# Setup path for local testing.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

# For signed cookies
from nitrogen.uri.query import Query


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
            if key == 'path' and value is None:
                value = '/'
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
        return raw_string.decode('utf8', 'replace')
    
    @staticmethod
    def _dumps(value):
        """Overide me to provide more sophisticated encoding."""
        if isinstance(value, unicode):
            return value.encode('utf8', 'replace')
        return str(value).decode('utf8', 'replace').encode('utf8')

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
            if isinstance(key, unicode):
                try:
                    key = key.encode('ascii')
                except UnicodeError:
                    raise Error("Illegal key value: %r." % key)
            if "" != key.translate(_idmap, _legal_chars):
                raise Error("Illegal key value: %r" % key)
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

def make_signed_container(hmac_key, maxage=None):
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
        u'value'
        
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
        u'this expires'
        
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
                query['s'] = hmac.new(hmac_key, str(query), hashlib.md5).hexdigest()
                return str(query)
            
            @staticmethod
            def _loads(value):
                try:
                    query = Query(value)
                    sig = query['s']
                    del query['s']
                    if hmac.new(hmac_key, str(query), hashlib.md5).hexdigest() != sig:
                        raise Error("Bad signature.")
                    if 'x' in query and int(query['x']) < time.time():
                        raise Error("Expired cookie.")
                    return query['v']
                except Exception as e:
                    raise Error(str(e))

    return SignedContainer

if __name__ == "__main__":
    from test import run
    run()



