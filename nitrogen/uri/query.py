from .. import sign


class Query(dict):
    
    def __init__(self, input=None, **kwargs):
        if isinstance(input, basestring):
            self.update(sign.decode_query(input))
        elif input is not None:
            self.update(input)
        if kwargs:
            self.update(kwargs)
    
    def sign(self, key, **kwargs):
        self.update(sign.sign_query(key, self))
    
    def verify(self, key, **kwargs):
        return sign.verify_query(key, self)
    
    def __str__(self):
        return sign.encode_query(self)
