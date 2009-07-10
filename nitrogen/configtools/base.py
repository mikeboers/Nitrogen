import sys
import logging

# The lowest level of log that the system should consider.
# Note that individual handlers can have a higher threshold than this.
log_level = logging.DEBUG

# The log handlers to register. Elements of this list should be fully setup
# and ready to be added to a logger. You can set the level of individual
# handlers via the setLevel method. For much more information, see:
# http://docs.python.org/library/logging.html .
log_handlers = [
    logging.StreamHandler(sys.stderr)
]

# The key to use to sign cookies. PLEASE set this to something different in
# the application configuration. If this is None, then a normal cookie
# container will be used, and nothing will be signed.
cookie_hmac_key = 'Please set this in nitrogenconfig.py for the application.'