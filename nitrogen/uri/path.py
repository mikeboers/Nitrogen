# coding: UTF-8
"""Module for query.Path object."""

from transcode import *

class PathError(ValueError):
    pass

class Path(list):
    u"""A representation of a path in a URI.
    
    Passed objects will only be parsed as a string if they extend the
    basestring. Otherwise they will be treated as a list of string segments.
    
    The absolute attribute will be determined automatically for strings, and
    as such the parameter to the contructor will have no influence whatsoever.
    
    This object has all list methods, except a different repr and str, as well
    as a pair of absolute/relative parameters (which automatically reflect
    each other).
    
    Basic examples:
    
        >>> path = Path('/absolute/path/to/something')
        >>> path
        <uri.Path:absolute:[u'absolute', u'path', u'to', u'something']>
        >>> str(path)
        '/absolute/path/to/something'
        
        >>> path = Path('relative/path/to/something')
        >>> path
        <uri.Path:relative:[u'relative', u'path', u'to', u'something']>
        >>> str(path)
        'relative/path/to/something'
    
    Switching to/from relative/absolute:
    
        >>> path = Path('some/path')
        >>> str(path)
        'some/path'
        >>> path.absolute = True
        >>> str(path)
        '/some/path'
        >>> path.relative = True
        >>> str(path)
        'some/path'
    
    Basic modifications:
    
        >>> path = Path('/some/path/to/stuff')
        >>> path.pop(0)
        u'some'
        >>> str(path)
        '/path/to/stuff'
        >>> path.pop()
        u'stuff'
        >>> str(path)
        '/path/to'
    
    Empty paths:
    
        >>> path = Path('/')
        >>> path
        <uri.Path:absolute:[]>
        >>> str(path)
        '/'
        
        >>> path = Path('')
        >>> path
        <uri.Path:relative:[]>
        >>> str(path)
        ''
        
        >>> path.relative = False
        >>> str(path)
        '/'
    
    Conforming to RFC section 3.3
    
        >>> path = Path('there:is/a_colon')
        >>> path.str()
        'there:is/a_colon'
        >>> path.str(scheme=False)
        Traceback (most recent call last):
        ...
        PathError: cannot have colons in first part of relative path with no scheme
        >>> path.str(scheme=False, strict=False)
        'there%3Ais/a_colon'
        
        >>> path = Path('//empty/first/section')
        >>> path.str()
        '//empty/first/section'
        >>> path.str(authority=False)
        Traceback (most recent call last):
        ...
        PathError: cannot have initial empty segments without authority
        >>> path.str(authority=False, strict=False)
        '/empty/first/section'
        
        >>> path = Path('////colon:resides/in/first_non_empty_section')
        >>> path.str()
        '////colon:resides/in/first_non_empty_section'
        >>> path.str(scheme=False, authority=False)
        Traceback (most recent call last):
        ...
        PathError: cannot have initial empty segments without authority
        >>> path.str(scheme=False, authority=False, strict=False)
        '/colon:resides/in/first_non_empty_section'
        
        >>> path = Path('colon:resides/in/first_section')
        >>> path.str()
        'colon:resides/in/first_section'
        >>> path.str(scheme=False)
        Traceback (most recent call last):
        ...
        PathError: cannot have colons in first part of relative path with no scheme
        >>> path.str(scheme=False, strict=False)
        'colon%3Aresides/in/first_section'
        >>> path.str(scheme=True)
        'colon:resides/in/first_section'
        >>> path.str(authority=False)
        'colon:resides/in/first_section'
        >>> path.str(authority=True)
        Traceback (most recent call last):
        ...
        PathError: must be empty or absolute with authority
        >>> path.str(authority=True, strict=False)
        '/colon:resides/in/first_section'
        >>> path.str(scheme=False, authority=True)
        Traceback (most recent call last):
        ...
        PathError: must be empty or absolute with authority
        >>> path.str(scheme=False, authority=True, strict=False)
        '/colon:resides/in/first_section'
        >>> path.str(scheme=False, authority=False)
        Traceback (most recent call last):
        ...
        PathError: cannot have colons in first part of relative path with no scheme
        >>> path.str(scheme=False, authority=False, strict=False)
        'colon%3Aresides/in/first_section'
        >>> path.str(scheme=True, authority=True)
        Traceback (most recent call last):
        ...
        PathError: must be empty or absolute with authority
        >>> path.str(scheme=True, authority=True, strict=False)
        '/colon:resides/in/first_section'
        >>> path.str(scheme=True, authority=False)
        'colon:resides/in/first_section'
        
        >>> path = Path('relative/path')
        >>> path.str(authority=True)
        Traceback (most recent call last):
        ...
        PathError: must be empty or absolute with authority
        >>> path.str(authority=True, strict=False)
        '/relative/path'
    
    remove_dot_segments from RFC section 5.2.4:
    
        >>> path = Path('/a/b/c/./../../g')
        >>> path.remove_dot_segments()
        >>> str(path)
        '/a/g'
        
        >>> path = Path('mid/content=5/../6')
        >>> path.remove_dot_segments()
        >>> str(path)
        'mid/6'
        
        >>> path = Path('a/b/c/.')
        >>> path.remove_dot_segments()
        >>> str(path)
        'a/b/c/'
        
        >>> path = Path('a/b/c/..')
        >>> path.remove_dot_segments()
        >>> str(path)
        'a/b/'
    
    Unicode:
    
        >>> path = Path('%C2%A1%E2%84%A2%C2%A3/%C2%A2%E2%88%9E%C2%A7/%C2%B6%E2%80%A2%C2%AA/%C2%BA')
        >>> print '/'.join(path)
        ¡™£/¢∞§/¶•ª/º
        
        >>> path = Path([u'¡™£', u'¢∞§', u'¶•ª', u'º'])
        >>> str(path)
        '%C2%A1%E2%84%A2%C2%A3/%C2%A2%E2%88%9E%C2%A7/%C2%B6%E2%80%A2%C2%AA/%C2%BA'
        
    """
    
    def __init__(self, input=None, absolute=False):
        self.absolute = absolute
        if input is None:
            return
        if isinstance(input, basestring):
            self.absolute = input and input[0] == '/'
            if self.absolute:
                input = input[1:]
            if input:
                self.extend(decode(x) for x in input.split('/'))
        else:
            self.extend(unicoder(x) for x in input)
    
    @property
    def relative(self):
        return not self.absolute
    
    @relative.setter
    def relative(self, value):
        self.absolute = not value
    
    def str(self, scheme=None, authority=None, strict=True):
        encoded = [encode(x, SUB_DELIMS + '@:') for x in self]
        # If there is no authority we must not have empty segments on the front.
        if authority is not None and not authority:
            while encoded and not encoded[0]:
                if strict:
                    raise PathError('cannot have initial empty segments without authority')
                encoded.pop(0)
        # Encode a colon in the first chunk if we have been told there is no
        # scheme, and this is relative.
        if self.relative and encoded and scheme is not None and not scheme and not authority:
            if strict and ':' in encoded[0]:
                raise PathError('cannot have colons in first part of relative path with no scheme')
            encoded[0] = encoded[0].replace(':', encode(':'))
        # If we have an authority, we must either be empty, or start with '/'
        if strict and not self.absolute and (authority and encoded):
            raise PathError('must be empty or absolute with authority')
        slash = '/' if (self.absolute or (authority and encoded)) else ''
        return slash + '/'.join(encoded)
    
    __str__ = str
    
    def __repr__(self):
        return '<uri.Path:%s:%s>' % (('absolute' if self.absolute else 'relative'), list.__repr__(self))
    
    def remove_dot_segments(self):
        i = 0
        while i < len(self):
            # print i, self[i], list(self)
            if self[i] == '.':
                if i == len(self) - 1:
                    self[i] = ''
                else:
                    self.pop(i)
            elif self[i] == '..':
                if i == len(self) - 1:
                    self.pop(i)
                    if i > 0:
                        self[i-1] = ''
                else:
                    self.pop(i)
                    if i > 0:
                        self.pop(i-1)
                        i -= 1
            else:
                i += 1

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '..')
    from test import run
    run()