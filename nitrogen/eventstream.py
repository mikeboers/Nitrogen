from . import request


def encode(data=None, event=None, id=None, retry=None):
    ret = []
    for name, value in [
        ('event', event),
        ('id', id),
        ('retry', retry),
        ('data', data)
    ]:
        if value:
            name = '%s: ' % name
            ret.append(name + str(value).replace('\n', '\n' + name))
    if ret:
        return '\n'.join(ret) + '\n\n'
    return ''


class Event(object):
    
    def __init__(self, data=None, event=None, id=None, retry=None):
        self.data = data
        self.event = event
        self.id = id
        self.retry = retry
    
    def __str__(self):
        return encode(self.data, self.event, self.id, self.retry)


class Response(request.Response):
    
    default_mimetype = 'text/event-stream'
    
    # Charset is ignored, but we are matching the old api.
    def iter_encoded(self, charset=None):
        charset = self.charset
        for item in self.response:
            if isinstance(item, unicode):
                yield encode(item.encode(charset))
            elif isinstance(item, str):
                yield encode(item)
            else:
                yield str(item)
    
