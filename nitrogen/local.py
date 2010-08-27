

_special_method_names = set(('__abs__', '__add__', '__and__',
    '__cmp__', '__coerce__', '__complex__',
    '__contains__','__delitem__',
    '__delslice__', '__dict__', '__div__', '__divmod__', '__enter__',
    '__eq__', '__exit__', '__float__', '__floordiv__',
    '__ge__',
    '__getitem__', '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__',
    '__iand__', '__idiv__', '__ifloordiv__', '__ilshift__', '__imod__',
    '__imul__', '__index__', '__instancecheck__', '__int__',
    '__invert__', '__iop__', '__ior__', '__ipow__', '__irshift__', '__isub__',
    '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', '__long__',
    '__lshift__', '__lt__', '__mod__',
    '__mul__', '__ne__', '__neg__', '__nonzero__',
    '__oct__', '__op__', '__or__', '__pos__', '__pow__', '__radd__', '__rand__',
    '__rcmp__', '__rdiv__', '__rdivmod__', '__repr__', '__reversed__',
    '__rfloordiv__', '__rlshift__', '__rmod__', '__rmul__', '__rop__', '__ror__',
    '__rpow__', '__rrshift__', '__rshift__', '__rsub__', '__rtruediv__',
    '__rxor__', '__setitem__',
    '__setslice__', '__str__', '__sub__', '__subclasscheck__',
    '__truediv__', '__unicode__', '__xor__'))
    

class LocalProxyMeta(type):
    
    def __new__(mcls, name, bases, ns):
        for name in _special_method_names:
            if name in ns:
                continue
            ns[name] = mcls.make_special_proxy(name)
        return super(LocalProxyMeta, mcls).__new__(mcls, name, bases, ns)
    
    @staticmethod
    def make_special_proxy(name):
        def special_method(self, *args, **kwargs):
            return getattr(self._object, name)(*args, **kwargs)
        return special_method
    
    
class LocalProxy(object):
    
    __metaclass__ = LocalProxyMeta
    
    def __init__(self, local, name):
        self._local = local
        self._name = name
    
    @property
    def _object(self):
        return getattr(self._local, self._name)
    
    def __getattribute__(self, name):
        if name.startswith('_'):
            return super(LocalProxy, self).__getattribute__(name)
        return getattr(self._object, name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(LocalProxy, self).__setattr__(name, value)
        else:
            setattr(self._object, name, value)
        
    def __repr__(self):
        return '<LocalProxy of %r at 0x%x by %r>' % (self._object, id(self._object), self._name)

if __name__ == '__main__':
    from threading import local
    l = local()
    l.test = []
    x = LocalProxy(l, 'test')
    x.append(1)
    print x
    print repr(x)
    print x.pop()