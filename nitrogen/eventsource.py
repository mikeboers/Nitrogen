mimetype = 'text/event-stream'

def event(data=None, event=None, id=None, retry=None):
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
