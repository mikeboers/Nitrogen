import os
import sys
import logging

# The lowest level of log that the system should consider.
# Note that individual handlers can have a higher threshold than this.
log_level = logging.DEBUG

# The log handlers to register. Elements of this list should be fully setup
# and ready to be added to a logger. You can set the level of individual
# handlers via the setLevel method. For much more information, see:
# http://docs.python.org/library/logging.html .
stderr_log_handler = logging.StreamHandler(sys.stderr)
log_handlers = [
    stderr_log_handler
]

# The key to use to sign cookies. PLEASE set this to something different in
# the application configuration. If this is None, then a normal cookie
# container will be used, and nothing will be signed.
hmac_key = 'Please set this in nitrogenconfig.py for the application.'

# The URI to use to create the sqlalchemy engine.
# Defaults to an in-memory database that will not be saved.
database_uri = 'sqlite:///:memory:'

# Where to look for templates, in order. It is recommended that you insert
# your directory on the front of this list.
template_path = [os.path.abspath(__file__ + '/../../templates')]