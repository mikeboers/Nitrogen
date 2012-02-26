import os
import logging
import sys

root = os.path.dirname(os.path.abspath(__file__))

debug = True

log_handlers = [logging.StreamHandler(sys.stderr)]

auth_login_url = '/auth/login'

sqlalchemy_url = 'sqlite:///' + root + '/database.sqlite'
sqlalchemy_echo = False

private_key = os.urandom(128)
    
template_path = [root + '/templates']
template_cache_dir = root + '/templates'

session_type = 'ext:database'
session_url = 'sqlite:///' + root + '/sessions.sqlite'
session_lock_dir = '/tmp/' + __name__
    
recaptcha_private_key = '6LdCprwSAAAAALD_xUJfPSp0uG-prJFLydoZJ-Ro'
recaptcha_public_key = '6LdCprwSAAAAALonrXY3m6LtMEEVh4ZVZi0pZ04n'
