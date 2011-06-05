
import os
import sys
import posixpath
import mimetypes
from time import time
from zlib import adler32
import logging

from werkzeug import Headers, wrap_file

import webstar.core as core

from .request import Request, Response


log = logging.getLogger(__name__)


# This entire function was lifted from flask.helpers. I don't like this sort
# of copy-pasta, but I've gotta. I have modified it ever so slightly so that
# we don't need flask installed. I have added the `response_class` and
# `use_x_sendfile` arguments. 

def send_file(filename_or_fp, environ=None, mimetype=None, as_attachment=False,
              attachment_filename=None, add_etags=True,
              cache_timeout=60 * 60 * 12, conditional=False,
              response_class=Response, use_x_sendfile=False):
    """Sends the contents of a file to the client.  This will use the
    most efficient method available and configured.  By default it will
    try to use the WSGI server's file_wrapper support.  Alternatively
    you can set the application's :attr:`~Flask.use_x_sendfile` attribute
    to ``True`` to directly emit an `X-Sendfile` header.  This however
    requires support of the underlying webserver for `X-Sendfile`.

    By default it will try to guess the mimetype for you, but you can
    also explicitly provide one.  For extra security you probably want
    to sent certain files as attachment (HTML for instance).  The mimetype
    guessing requires a `filename` or an `attachment_filename` to be
    provided.

    Please never pass filenames to this function from user sources without
    checking them first.  Something like this is usually sufficient to
    avoid security problems::

        if '..' in filename or filename.startswith('/'):
            abort(404)

    .. versionadded:: 0.2

    .. versionadded:: 0.5
       The `add_etags`, `cache_timeout` and `conditional` parameters were
       added.  The default behaviour is now to attach etags.

    .. versionchanged:: 0.7
       mimetype guessing and etag support for file objects was
       deprecated because it was unreliable.  Pass a filename if you are
       able to, otherwise attach an etag yourself.  This functionality
       will be removed in Flask 1.0

    :param filename_or_fp: the filename of the file to send.  This is
                           relative to the :attr:`~Flask.root_path` if a
                           relative path is specified.
                           Alternatively a file object might be provided
                           in which case `X-Sendfile` might not work and
                           fall back to the traditional method.
    :param mimetype: the mimetype of the file if provided, otherwise
                     auto detection happens.
    :param as_attachment: set to `True` if you want to send this file with
                          a ``Content-Disposition: attachment`` header.
    :param attachment_filename: the filename for the attachment if it
                                differs from the file's filename.
    :param add_etags: set to `False` to disable attaching of etags.
    :param conditional: set to `True` to enable conditional responses.
    :param cache_timeout: the timeout in seconds for the headers.
    """
    mtime = None
    if isinstance(filename_or_fp, basestring):
        filename = filename_or_fp
        file = None
    else:
        from warnings import warn
        file = filename_or_fp
        filename = getattr(file, 'name', None)

        # XXX: this behaviour is now deprecated because it was unreliable.
        # removed in Flask 1.0
        if not attachment_filename and not mimetype \
           and isinstance(filename, basestring):
            warn(DeprecationWarning('The filename support for file objects '
                'passed to send_file is not deprecated.  Pass an '
                'attach_filename if you want mimetypes to be guessed.'),
                stacklevel=2)
        if add_etags:
            warn(DeprecationWarning('In future flask releases etags will no '
                'longer be generated for file objects passed to the send_file '
                'function because this behaviour was unreliable.  Pass '
                'filenames instead if possible, otherwise attach an etag '
                'yourself based on another value'), stacklevel=2)

    # Removed this check for nitrogen.
    # if filename is not None:
    #     if not os.path.isabs(filename):
    #         filename = os.path.join(current_app.root_path, filename)
    
    if mimetype is None and (filename or attachment_filename):
        mimetype = mimetypes.guess_type(filename or attachment_filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            if filename is None:
                raise TypeError('filename unavailable, required for '
                                'sending as attachment')
            attachment_filename = os.path.basename(filename)
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    if use_x_sendfile and filename:
        if file is not None:
            file.close()
        headers['X-Sendfile'] = filename
        data = None
    else:
        if file is None:
            file = open(filename, 'rb')
            mtime = os.path.getmtime(filename)
        data = wrap_file(environ, file) if environ else file

    rv = response_class(data, mimetype=mimetype, headers=headers,
                                    direct_passthrough=True)

    # if we know the file modification date, we can store it as the
    # current time to better support conditional requests.  Werkzeug
    # as of 0.6.1 will override this value however in the conditional
    # response with the current time.  This will be fixed in Werkzeug
    # with a new release, however many WSGI servers will still emit
    # a separate date header.
    if mtime is not None:
        rv.date = int(mtime)

    rv.cache_control.public = True
    if cache_timeout:
        rv.cache_control.max_age = cache_timeout
        rv.expires = int(time() + cache_timeout)

    if add_etags and filename is not None:
        rv.set_etag('flask-%s-%s-%s' % (
            os.path.getmtime(filename),
            os.path.getsize(filename),
            adler32(filename) & 0xffffffff
        ))
        if conditional and environ:
            rv = rv.make_conditional(environ)
            # make sure we don't send x-sendfile for servers that
            # ignore the 304 status code for x-sendfile.
            if rv.status_code == 304:
                rv.headers.pop('x-sendfile', None)
    return rv


class WSGIWrapper(object):
    
    def __init__(self, path):
        self.path = path
    
    @Request.application
    def __call__(self, request):
        use_x_sendfile = False #request.environ.get('SERVER_SOFTWARE', '').startswith('Apache')
        return send_file(self.path,
            environ=request.environ,
            conditional=True,
            use_x_sendfile=use_x_sendfile
        )
        
        
class StaticRouter(core.RouterInterface):
    
    def __init__(self, path, data_key='filename'):
        self.path = path
        self.data_key = data_key
        super(StaticRouter, self).__init__()
    
    def route_step(self, path):
        path = path[1:]
        if not path:
            return
        for base in self.path:
            fullpath = os.path.join(base, path)
            if os.path.exists(fullpath) and os.path.isfile(fullpath):
                yield core.RouteStep(
                    head=WSGIWrapper(fullpath),
                    router=self,
                    consumed=path,
                    unrouted='',
                    data={self.data_key: path},
                )
    
    def generate_step(self, data):
        path = data.get(self.data_key)
        if path is not None:
            yield core.GenerateStep(segment=path, head=None)



