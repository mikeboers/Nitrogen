# coding: UTF-8
"""Module for query.Userinfo object."""

from transcode import *

class Userinfo(list):
    u"""A representation of the userinfo segment in a URI.
    
    Passed objects will only be parsed as a string if they extend the
    basestring. Otherwise they will be treated as a list of string segments.
    
    This object has all list methods, except a different repr and str, as well
    as a pair of absolute/relative parameters (which automatically reflect
    each other).
    
    Basic parsing:
        
        >>> userinfo = Userinfo('user:pass')
        >>> userinfo
        <uri.Userinfo:[u'user', u'pass']>
        >>> str(userinfo)
        'user:pass'
    
    Modifications:
    
        >>> userinfo = Userinfo()
        >>> userinfo.append('user')
        >>> str(userinfo)
        'user'
        >>> userinfo.append('pass')
        >>> str(userinfo)
        'user:pass'
    
    Encoding:
    
        >>> userinfo = Userinfo(['something with spaces'])
        >>> userinfo
        <uri.Userinfo:['something with spaces']>
        >>> str(userinfo)
        'something%20with%20spaces'
    
    Decoding:
        
        >>> userinfo = Userinfo('something%20with%20spaces')
        >>> userinfo
        <uri.Userinfo:[u'something with spaces']>
        >>> str(userinfo)
        'something%20with%20spaces'
    
    Empty userinfo:
    
        >>> userinfo = Userinfo()
        >>> userinfo
        <uri.Userinfo:[]>
        >>> str(userinfo)
        ''
        
        >>> userinfo = Userinfo('')
        >>> userinfo
        <uri.Userinfo:[]>
        >>> str(userinfo)
        ''
    
    Unicode:

        >>> userinfo = Userinfo('%C2%A1%E2%84%A2%C2%A3:%C2%A2%E2%88%9E%C2%A7:%C2%B6%E2%80%A2%C2%AA:%C2%BA')
        >>> print ':'.join(userinfo)
        ¡™£:¢∞§:¶•ª:º

        >>> userinfo = Userinfo([u'¡™£', u'¢∞§', u'¶•ª', u'º'])
        >>> str(userinfo)
        '%C2%A1%E2%84%A2%C2%A3:%C2%A2%E2%88%9E%C2%A7:%C2%B6%E2%80%A2%C2%AA:%C2%BA'
    """
    
    def __init__(self, input=None):
        if input is None:
            return
        if isinstance(input, basestring):
            if input:
                self.extend(decode(x) for x in input.split(':'))
        else:
            self.extend(input)

    def __str__(self):
        return ':'.join(encode(x, SUB_DELIMS) for x in self)
    
    def __repr__(self):
        return '<uri.Userinfo:%s>' % list.__repr__(self)

if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."