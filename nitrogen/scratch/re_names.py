

import re
import string
import base64

class Route(object):
    
    temp_key_chars = string.lowercase
    
    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            self.name = args[0]
            args = args[1:]
        self.raw = args[0]
        self.kwargs = kwargs
        self.group_keys = {}
        self.compiled = self.compile_re(self.raw)
    
    def _get_temp_key(self, index):
        key = ''
        while True:
            index, char = divmod(index, len(self.temp_key_chars))
            key += self.temp_key_chars[char]
            if index == 0:
                break
        return '_' + key
    
    def _compile_callback(self, match):
        name = match.group(1)
        pattern = match.group(2)
        if pattern is None:
            pattern = '[^/]*'
        key = name # self._get_temp_key(len(self.group_keys))
        self.group_keys[key] = name
        return '(?P<%s>%s)' % (name, pattern)

    def compile_re(self, raw):
        return re.sub(r'{([a-zA-Z_]\w*)(?::(.+?))?}', self._compile_callback, raw)
    
    def match(self, uri):
        m = re.match(self.compiled, uri)
        if not m:
            return None
        
        raw_kwargs = m.groupdict()
        named_spans = set(m.span(k) for k in raw_kwargs)

        args = [x for i, x in enumerate(m.groups()) if m.span(i + 1) not in named_spans]
        kwargs = self.kwargs.copy()
        kwargs.update(dict((self.group_keys[k], v) for k, v in raw_kwargs.items()))
        
        return args, kwargs
        



def compile_named_groups(raw, default_pattern='.*?'):
    def callback(match):
        name = match.group(1)
        pattern = match.group(2)
        if pattern is None:
            if default_pattern is None:
                return match.group(0)
            pattern = default_pattern
        return '(?P<%s>%s)' % (name, pattern)
    return re.sub(r'{([a-zA-Z_]\w*)(?::(.+?))?}', callback, raw)

def extract_named_groups(match):
    kwargs = m.groupdict()
    named_spans = set(m.span(k) for k in kwargs)
    args = [x for i, x in enumerate(m.groups()) if m.span(i + 1) not in named_spans]
    return args, kwargs
    
pattern = '/{controller}/(.+?)/{id:\d+}'
uri = '/gallery/photo/12'

compiled = compile_named_groups(pattern)
print compiled
m = re.match(compiled, uri)
print m
print extract_named_groups(m)
exit()

matcher = Route('name', pattern, blah='constant')
print matcher.compiled


m = matcher.match(uri)
print m