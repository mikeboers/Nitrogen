

def dict_from_attrs(obj, all=False):
    """Builds a dictionary of all attributes on a given object.

    Useful for modules which do not internally store everything in a __dict__
    attribute.

    Params:
        obj -- The object to pull attributes from.
        all -- Should we pull everything, or treat '_' prefixes as private?

    Returns:
        A dict.
    """
    return dict((k, getattr(obj, k)) for k in dir(obj)
        if all or not k.startswith('_'))