#!/usr/bin/env PATH=/Server/www/webapp/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin python2.6

import os
import sys
sys.path.append('/Server/www/webapp')

from webapp.wsgi.runners import run_via_cgi
from webapp.wsgi.middlewear import status_helper



def app(env, start):
    
    start(200, [
        ('Content-Type', 'text/plain')
    ])
    yield """This script demonstrates the usage of the status_helper middlewear.
There is nothing really interesting about this output, beyond it actually working.

"""
    
    yield 'ENVIRONMENT:\n'
    for k, v in sorted(env.items()):
        if k.split('_')[0] in 'HTTP SCRIPT SERVER QUERY boers'.split():
            yield '\t%s: %r\n' % (k, v)
    yield "\n"
    
app = status_helper(app)
run_via_cgi(app)