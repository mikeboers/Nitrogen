

def _static_attribute(value):
    @property
    def inner(self):
        return value
    return inner


class AnonymousUser(object):
    email = _static_attribute(None)
    email_is_verified = _static_attribute(False)
    is_anonymous = _static_attribute(True)
    is_authenticated = _static_attribute(False)
    is_superuser = _static_attribute(False)
    password = _static_attribute(None)    
    def has_perm(self, *args, **kwargs):
        return False