#!/usr/bin/env PATH=/Server/www/webapp:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin python2.6

import os
import sys
sys.path.append('/Server/www/webapp')

import cgi
from webapp.wsgi.runners import run_via_cgi
from webapp.wsgi.middlewear import full_parser
        
def app(env, start):
        
    start('200 OK', [('Content-Type', 'text/html')])
    
    yield '<pre>'
    yield __file__ + '\n'
    yield '\n'
    
    yield 'ENVIRONMENT:\n'
    for k, v in sorted(env.items()):
        yield '\t%s: %r\n' % (k, cgi.escape(str(v)))
    yield "\n"
    
    yield "COOKIES:\n"
    for k, v in sorted(env['boers.cookies'].items()):
        yield '\t%s: %r\n' % (k, cgi.escape(str(v)))
    yield "\n"
    
    yield "GET:\n"
    for k, v in sorted(env['boers.get'].items()):
        yield '\t%s: %r\n' % (k, cgi.escape(str(v)))
    yield "\n"
    
    yield "POST:\n"
    for k, v in sorted(env['boers.post'].items()):
        yield '\t%s: %r\n' % (k, cgi.escape(str(v)))
    yield "\n"
    
    yield """<form method="post" /><input type="text" name="posted_key" value="posted_value" />
<input type="submit" />
</form>"""
    

app = full_parser(app)
run_via_cgi(app)