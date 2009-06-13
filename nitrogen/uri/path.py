"""Module for query.Path object."""

from transcode import *

class Path(list):
    """A representation of a path in a URI.
    
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
        <uri.Path:absolute:['absolute', 'path', 'to', 'something']>
        >>> print path
        /absolute/path/to/something
        
        >>> path = Path('relative/path/to/something')
        >>> path
        <uri.Path:relative:['relative', 'path', 'to', 'something']>
        >>> print path
        relative/path/to/something
    
    Switching to/from relative/absolute:
    
        >>> path = Path('some/path')
        >>> print path
        some/path
        >>> path.absolute = True
        >>> print path
        /some/path
        >>> path.relative = True
        >>> print path
        some/path
        
    """
    
    def __init__(self, input=None, absolute=False):
        self.absolute = absolute
        if not input:
            return
        if isinstance(input, basestring):
            self.absolute = input and input[0] == '/'
            if self.absolute:
                input = input[1:]
            self.extend(decode(x) for x in input.split('/'))
        else:
            self.extend(str(x) for x in input)
    
    @property
    def relative(self):
        return not self.absolute
    
    @relative.setter
    def relative(self, value):
        self.absolute = not value
    
    def __str__(self):
        return ('/' if self.absolute else '') + '/'.join(encode(x, SUB_DELIMS + '@:') for x in self)
    
    def __repr__(self):
        return '<uri.Path:%s:%s>' % (('absolute' if self.absolute else 'relative'), list.__repr__(self))

if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."