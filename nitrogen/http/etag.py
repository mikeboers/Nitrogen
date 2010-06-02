
import hashlib

from ..request import Request, Response


def etagger(app):
    def etagger_app(environ, start):
        
        state = dict(
            status=None,
            headers=None
        )
        def inner_start(status, headers, exc_info=None):
            state.update(dict(
                status=status,
                headers=headers
            ))
        
        output = ''.join(app(environ, inner_start))
        
        # If the status is anything but a 200 OK then don't touch it.
        code = int(str(state['status']).split()[0])
        if code != 200:
            start(state['status'], state['headers'])
            yield output
            return
        
        etag = 'md5=' + hashlib.md5(output).hexdigest()
        
        req = Request(environ=environ)
        res = Response(start=start, headers=state['headers'])
        
        if res.etag is None:
            res.etag = etag
            if req.etag == etag:
                res.start('304 Not Modified')
                return
        
        res.start(state['status'])
        yield output
    
    return etagger_app