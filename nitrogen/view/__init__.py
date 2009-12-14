'''nitrogen.view package'''

# Some constants for the two most common Content-Type headers. These are being
# depreciated, as the request object (which is in use much more often) does
# this all for us.
TYPE_HEADER_HTML = ('Content-Type', 'text/html;charset=UTF-8')
TYPE_HEADER_TEXT = ('Content-Type', 'text/plain;charset=UTF-8')