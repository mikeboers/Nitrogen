import os
import sys
import logging
import tools

# The log handlers to register. Elements of this list should be fully setup
# and ready to be added to a logger. You can set the level of individual
# handlers via the setLevel method. For much more information, see:
# http://docs.python.org/library/logging.html .

# For use as key material. Feel free to slice this up. This is assumed to always
# be atleast 512 bits (64 bytes) long. Notice that it is being decoded from hex
# into a binary string. This can easily be built by running:
#   python -c "import os, hashlib; print hashlib.sha512(os.urandom(8096)).hexdigest()"
# crypto_entropy = 'Please set this in nitrogenconfig.py for the application.'


# Where to look for templates, in order. It is recommended that you insert
# your directory on the front of this list.
template_path = [os.path.abspath(__file__ + '/../../templates')]


servers = tools.ServerList()
