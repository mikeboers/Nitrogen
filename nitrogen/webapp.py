from __future__ import print_function

import sys
import os
import cgi
import wsgiref.handlers
import cStringIO
import traceback
import threading
import logging

from . import cookie

cookie_lock = threading.Lock()

class FieldStorage(cgi.FieldStorage):
    '''Extension of cgi.FieldStorage that redefines most of the access methods.'''
    
    
    def __init__(self, fp=None, headers=None, outerboundary="",
                 environ=os.environ, keep_blank_values=0, strict_parsing=0):
        
        self.app = environ.get('boers.app', None)
        
        self.FieldStorageClass = self.__class__
        cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
                     environ, keep_blank_values, strict_parsing)
    
    def iterkeys(self):
        return (x.name for x in self.list)
    
    def keys(self):
        return list(self.iterkeys())
    
    def iteritems(self):
        return ((x.name, x.value) for x in self.list)
    
    def items(self):
        return list(self.iteritems())
    
    def get(self, key, default=None):
        if self.list is None:
            raise TypeError, "not indexable"
        if isinstance(key, int):
            return self.list[key]
        for item in self.list:
            if item.name == key:
                return item
        return default
    
    def __getitem__(self, key):
        item = self.get(key)
        if item is None:
            raise KeyError, key
        return item
                
    def get_list(self, key):
        '''Similar to getfirst, but returns the object instead of the value.'''
        found = []
        if self.list is None:
            raise TypeError('Not indexable.')
        for item in self.list:
            if item.name == key:
                found.append(item)
        return found
    
    def get_value(self, key, default=None):
        item = self.get(key)
        return item.value if item is not None else default
    
    def get_value_list(self, key):
        return list(x.value for x in self.get_list(key))
    
    def getvalue(self, key, default=None):
        raise AttributeError('getvalue')
    
    def getfirst(self, key, default=None):
        raise AttributeError('getfirst')
    
    def getlist(self, key, default=None):
        raise AttributeError('getlist')
    
    def make_file(self, binary=None):
        raise ValueError('Not accepting posted files.')
    
    def __len__(self):
        return len(self.list) if self.list else 0
    
    def __repr__(self):
        return "%s(key=%r, filename=%r)" % (self.__class__.__name__, self.name, self.filename)



class HeaderList(list):
    '''A more dict-like list for headers.'''
    
    def __setitem__(self, key, value):
        '''Appends a header with item access.
        
        Does not check to see if the header is already set. Multiple headers
        with the same key can be created this way.
        
        '''
        if isinstance(key, str):
            self.append((key, value))
        else:
            list.__setitem__(self, key, value)
    
    def __delitem__(self, key):
        '''Delete by index, or header type.'''
        if isinstance(key, str):
            # Go backwards through self, removing headers with the same key
            for i in xrange(len(self) - 1, -1, -1):
                if self[i][0] == key:
                    list.__delitem(self, i)
        else:
            list.__delitem__(self, key)

class WebApp(object):
    
    '''A simple web application.
    
    Provides a simple interface to common web application tools, such as GET
    (querystring) data, POST data, cookies (with ability to read, modify, and
    create), http status codes and headers.
    
    Overide the main() method in child classes to provide main functinality
    of your application.
    
    wsgiref handlers expect the result of the callable they are given as the
    application to be an iterator. When called, the class instantiated itself
    and the instance is itself iterable. When the iterable functionality is
    requested, it sets up an output buffer, calls it's main() method (which is
    expected to be overiden for the individual application), send the HTTP
    status and headers (which may be modified during the main() call), and
    returns a single element list with the captured output.
    
    Usage:
        Overide this class and pass the new class to a wsgiref handler.
    
    '''
    
    FieldStorageClass = FieldStorage
    CookieContainerClass = cookie.Container
    
    @classmethod
    def run_via_cgi(cls):
        '''Run the web application with the wsgiref CGI handler.'''
        wsgiref.handlers.CGIHandler().run(cls)
    
    @classmethod
    def run_via_fcgi(cls, thread_safe=False):
        from .fcgi import WSGIServer
        WSGIServer(cls, multithreaded=thread_safe).run()
    
    def __init__(self, env, start_callback):
        '''Initialize the application.
        
        Arguments:
            env -- The environment to run the app in.
            start_callback -- The function to call to define the HTTP status
                and headers.
        
        Sets up:
            - Environment (env).
            - Query Data (get).
            - Cookies.
            - HTTP status and headers.
        
        Handling of posted data is delayed until an iterator is requested. If
        you want to do something after env, get, or cookie are in place, but
        before posted data is parsed, extend the before_handling_post()
        method.
        '''
        
        
        self.env = env
        self.env['boers.app'] = self
        
        # Parse the query data (get).
        # Need to force it to not see stdin, and to only try to parse the
        # query string.
        get_env = self.env.copy()
        get_env['REQUEST_METHOD'] = 'GET'
        self.get = self.FieldStorageClass(
            fp=None,
            environ=get_env,
            keep_blank_values=True
        )
        # Parse cookies (with my class.)
        self.cookies = self.CookieContainerClass(env.get('HTTP_COOKIE', ''))
        # Initialize HTTP status and header containers.
        self.status = '200 OK'
        self.headers = HeaderList()
        # Store the start_call back for when we need it, and initialize the
        # output buffer that will catch printed output while calling main().
        self._start_callback = start_callback
        # Init attributes we will use later
        self.post = None
        self._output_buffer = None
    
    def __iter__(self):
        '''Run the application and return the output as a single element list.
        
        '''
        
        # Setup the output buffer that works with self.write(...) and self.print(...).
        self._output_buffer = cStringIO.StringIO()
        
        try:
            self.before_handling_post()
            # Parse posted data.
            # It must be forced to not see the query string, so it is only
            # POSTed data.
            post_env = self.env.copy()
            post_env['QUERY_STRING'] = ''
            self.post = self.FieldStorageClass(
                fp=self.env['wsgi.input'],
                environ=post_env,
                keep_blank_values=True
            )
            
            # Main!
            self.main()
            
            # Append cookies to header.
            # Something in here is NOT thread-safe. I think it is the encrypted cookies.
            cookie_lock.acquire()
            self.headers.extend(self.cookies.build_headers())
            cookie_lock.release()
            
            # Start the WSGI callback
            self._start_callback(self.status, list(self.headers))
            
            for x in self.iter():
                yield x
            
        except Exception as e:
            logging.exception('500 Server Error')
            for x in self.handle_exception():
                yield x
        finally:
            self.finished_request()
    
    def handle_exception(self):
        # Need to grab the traceback before yielding otherwise the
        # traceback.format_exc(...) will not give us anything back.
        tb = traceback.format_exc()
        self._start_callback('500 Server Error', [
            ('Content-Type', 'text/plain')
        ])
        yield 'UNCAUGHT EXCEPTION\n\n'
        yield tb
        yield '\n'
        if self._output_buffer:
            yield 'BUFFERED OUTPUT\n\n'
            yield self._output_buffer.getvalue()
    
    def write(self, *args, **kwargs):
        '''Wrapper for buffer write(...) method.
        
        Only works if the buffer exists.
        
        '''
        if self._output_buffer:
            self._output_buffer.write(*args, **kwargs)
    
    def print(self, *args, **kwargs):
        '''Wrapper for print(...) function.
        
        Only change is to set the default "file" kwarg to the output buffer
        if the buffer exists.
        
        '''
        
        if self._output_buffer:
            kwargs['file'] = kwargs.get('file', self._output_buffer)
            print(*args, **kwargs)
    
    @property
    def is_post(self):
        return self.env['REQUEST_METHOD'] == 'POST'
    
    @property
    def is_get(self):
        return self.env['REQUEST_METHOD'] == 'GET'
    
    
    def before_handling_post(self):
        '''Extend this method to do something with env, get or cookies before
        posted data is handled.
        
        You can do everything in here exactly the same as in main(), except
        self.post is not availible yet.
        
        This is only called if the http method is POST.
        
        '''
        
        pass
    
    def main(self):
        '''Called to produce main application functionality.
        
        Overide this method and set self.status, add to self.headers, take
        from self.get and self.post, modify self.cookies, and self.print() whatever
        data that should be output to the browser.
        
        You can set print to be self.print at the top of your main, and then
        everything print()ed will be sent into the buffer.
        
        Headers will be sent after main has been called.
        
        '''
        
        pass
    
    def iter(self):
        '''Build an iterator to give to WSGI.
        
        Overide this if you want to actually give back an iterator. Defaults
        to sending back buffered output.
        
        Note that the headers have been sent by this time, and if you are
        extending this method (but still calling it), self.write(...) and
        self.print(...) are only functional BEFORE calling this implementation
        of iter(...), because it yields the contents of the buffer.
        
        '''
        
        if self._output_buffer:
            yield self._output_buffer.getvalue()
    
    def finished_request(self):
        '''Called after all the items have been yielded from the iterator.
        
        Nothing done here can affect output in any way, and is still called in
        case of failure (an exception thrown by main(...) or iter(...).
        
        '''
        
        pass
