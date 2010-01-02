
from fnmatch import fnmatch
import logging

def basic_match(pattern, perm):
    """For checking a permission list to see if they have it.
    
    Basic examples:
    
        >>> basic_match('a', 'a')
        True
        >>> basic_match('a', 'b')
        False
    
    Patterns:
    
        >>> basic_match('a.*', 'a.a')
        True
        >>> basic_match('a.*', 'b.b')
        False
    
    Catch all pass:
    
        >>> basic_match('*', 'anything')
        True
    
    Hierarchical:
    
        >>> perms = ['a.one.two', '-a.one', 'a']
        >>> basic_match(perms, 'a')
        True
        >>> basic_match(perms, 'a.one')
        False
        >>> basic_match(perms, 'a.one.two')
        True
    
        
    """

    pattern = pattern.split('.')
    patterns = ['.'.join(pattern[:i]) for i in range(1, 1 + len(pattern))]
    
    logging.debug(patterns)
    logging.debug(perm)
    
    if any(fnmatch(pattern, perm) for pattern in patterns):
        return True
    return False



if __name__ == '__main__':
    
    from ..test import run
    run()

    
