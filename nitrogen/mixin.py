import werkzeug as wz
import werkzeug.utils


def build_from_mro(carrier_class, base_class, name=None):
    """Make a class from mixins in the inheritence chain of a parent class.
    
    Works backwards down the MRO of a parent class, collecting unique mixin
    classes named after the base object. Eg. if extending a Request class, this
    will look for RequestMixin classes.
    
    """
    name = name or base_class.__name__
    bases = []
    for cls in carrier_class.__mro__:
        mixin = getattr(cls, name + 'Mixin', None)
        if mixin and mixin not in bases:
            bases.append(mixin)
    bases.append(base_class)
    cls = type('%s.%s(mixin)' % (carrier_class.__name__, name), tuple(bases), {})
    cls.__module__ = carrier_class.__module__
    return cls


def builder_property(base):
    def _build_class(self):
        return build_from_mro(self.__class__, base)
    return wz.utils.cached_property(_build_class, name=base.__name__)
    