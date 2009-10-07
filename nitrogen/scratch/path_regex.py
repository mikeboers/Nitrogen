
import os
import re
import hashlib
import base64

class Route(object):
    """
    >>> r = Route(r'/{controller}/{action}/{id:\d+}')
    >>> r
    <Route:r'/{controller}/{action}/{id:\d+}'>
    
    >>> r.match('/gallery/photo/12')
    {'action': 'photo', 'controller': 'gallery', 'id': '12'}
    
    >>> r.match('/controller/action/12/extra')
    >>> r.match('/controller/action/12extra')
    >>> r.match('/controller/action/not_digits')
    
    >>> r.build(controller='news', action='archive', id='24')
    '/news/archive/24'
    
    >>> r = Route('/gallery/{action}', controller='gallery')
    >>> m = r.match('/gallery/view')
    >>> m
    {'action': 'view', 'controller': 'gallery'}
    >>> r.build(**m)
    '/gallery/view'
    
    >>> r = Route('/{id}', _requirements={'id': r'\d+'})
    >>> r.match('/12')
    {'id': '12'}
    >>> r.match('/hi')
    
    >>> r = Route('/{id:\d+}', _parsers={'id':int})
    >>> r.match('/12')
    {'id': 12}
    
    >>> r = Route('/{method:[A-Z]+}', _formatters={'method': str.upper})
    >>> r.match('/GET')
    {'method': 'GET'}
    >>> r.build(method='post')
    '/POST'
    
    
    """
    
    default_pattern = '[^/]*'
    token_re = re.compile(r"""
        {([a-zA-Z_]\w*)(?::(.+?))?}
        """, re.X)
    
    def __init__(self, *args, **kwargs):
        
        self.name = None
        if len(args) > 1:
            self.name = args[0]
            args = args[1:]
        
        self._raw = args[0]
        self._constants = kwargs
        
        self._requirements = kwargs.pop('_requirements', {})
        self._requirements = dict((k, re.compile(v + '$'))
            for k, v in self._requirements.items())
        
        self._parsers = kwargs.pop('_parsers', {})
        self._formatters = kwargs.pop('_formatters', {})
        
        self._compile()
        
    
    def __repr__(self):
        return '<Route:r%s>' % repr(self._raw).replace('\\\\', '\\')
    
    def _compile(self):
        
        self._hash_to_key = {}
        self._hash_to_pattern = {}
        
        format = self.token_re.sub(self._compile_sub, self._raw)
        
        pattern = re.escape(format)
        for hash, patt in self._hash_to_pattern.items():
            pattern = pattern.replace(hash, patt, 1)
        
        for hash, key in self._hash_to_key.items():
            format = format.replace(hash, '%%(%s)s' % key, 1)
        
        self.format = format
        self.compiled = re.compile(pattern + '$')
        
        del self._hash_to_key
        del self._hash_to_pattern
        
    def _compile_sub(self, match):
        name = match.group(1)
        patt = match.group(2) or self.default_pattern
        hash = 'x' + base64.b32encode(hashlib.md5(name).digest()).strip('=')
        self._hash_to_key[hash] = name
        self._hash_to_pattern[hash] = '(?P<%s>%s)' % (name, patt)
        return hash
    
    def match(self, value):
        m = self.compiled.match(value)
        if not m:
            return None
        
        result = self._constants.copy()
        result.update(m.groupdict())
        
        for key, pattern in self._requirements.items():
            if not key in result or not pattern.match(result[key]):
                return None
        
        for key, callback in self._parsers.items():
            if key in result:
                result[key] = callback(result[key])
        
        return result
    
    def build(self, **kwargs):
        for key, callback in self._formatters.items():
            if key in kwargs:
                kwargs[key] = callback(kwargs[key])
        return self.format % kwargs
            
        


if __name__ == '__main__':
    import doctest
    doctest.testmod()
