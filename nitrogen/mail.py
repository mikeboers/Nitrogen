# encoding: utf8
"""Wrapper around email and smtplib modules for the easy sending of mail.

"""

from email.encoders import encode_7or8bit
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr as _parse_addr, formataddr as _format_addr
from threading import RLock
import re
import smtplib
import socket
import string


def format_address(addr, strict=True):
    r"""Format an email address into a string.

    Accepts either a string (ie. "name <address>" or "address"), or a 2-tuple
    (ie. ("name", "address")), and returns a properly formatted string
    (ie. "name <address>").

    We do not attempt to escape bad input, but will raise an exception by
    default if we get it (such as a newline in an address).

    Examples:

        >>> format_address('mail@example.com')
        'mail@example.com'
        >>> format_address(('Mike Boers', 'mail@example.com'))
        'Mike Boers <mail@example.com>'

        >>> format_address('mail\n@example.com')
        Traceback (most recent call last):
        ...
        ValueError: bad address 'mail\n@example.com'

        >>> format_address('mail\n@example.com', False)
        'mail@example.com'
        >>> format_address(('name\nnewline', 'addr\nnewline'), False)
        'name newline <addrnewline>'
        >>> format_address('to@many@ats', False)
        'to@many'

    """
    if not isinstance(addr, basestring):
        addr = _format_addr(addr)
    out = _format_addr(_parse_addr(addr))
    if strict and out != addr:
        raise ValueError('bad address %r' % addr)
    return out


def format_address_list(addrs):
    """Format input meant as a list of addresses into a list of addresses.

    Accepts None, a single string, or a list of strings or 2-tuples. Returns
    a list (possibly empty) of formatted addresses.

    Raises an exception on a bad address.

    """
    if isinstance(addrs, basestring):
        addrs = [addrs]
    return [format_address(x) for x in addrs or []]


def format_mail(from_=None, to=None, subject=None, text=None, html=None,
    cc=None, bcc=None, attach=None, **kwargs):
    """Prepare all the parts of a message for sending.

    Takes the from, to, cc, and bcc address(es), subject, text and/or html
    content, and a list of attachments.

    The from can be specified as the first positional argument, or the keyword
    from_, or from.

    Returns a 3-tuple of the from adress, a list of to adresses, and the
    message to send as a string, ready for use with smtplib.

    Examples:

        >>> from_, to, msg = format_mail(to='test@example.com',
        ...     subject='TEST', text='text body', html='html body')
        >>> to
        ['test@example.com']
        >>> print msg #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Content-Type: multipart/alternative;
                boundary="===============...=="
        MIME-Version: 1.0
        Subject: TEST
        From: mailer@...
        To: test@example.com
        <BLANKLINE>
        --===============...==
        MIME-Version: 1.0
        Content-Transfer-Encoding: 7bit
        Content-Type: text/plain; charset="utf8"
        <BLANKLINE>
        text body
        --===============...==
        MIME-Version: 1.0
        Content-Transfer-Encoding: 7bit
        Content-Type: text/html; charset="utf8"
        <BLANKLINE>
        html body
        --===============...==--


    """

    if isinstance(text, unicode):
        text = text.encode('utf8')
    elif text is not None:
        text = str(text)

    if isinstance(html, unicode):
        html = html.encode('utf8')
    elif html is not None:
        html = str(html)

    if text is None and html is None:
        raise ValueError('must be given atleast either text or html')

    from_ = format_address(from_ or kwargs.get('from') or 'mailer@' +
        socket.gethostname())
    to = format_address_list(to)
    cc = format_address_list(cc)
    bcc = format_address_list(bcc)

    mail = MIMEMultipart('alternative')

    if subject is not None:
        # Only encode the subject if we need to.
        if re.match('[ a-zA-Z0-9' + re.escape(string.punctuation) + ']*$',
            subject):
            mail['Subject'] = subject
        else:
            mail['Subject'] = Header(subject, 'utf8')

    mail['From'] = from_
    mail['To'] = ', '.join(to)
    if cc:
        mail['Cc'] = ', '.join(cc)

    if attach is not None:
        for x in attach:
            mail.attach(x)

    # If we set the charset in the MIMEText constructor, the message gets
    # base64 encoded, which may be optimal for network safety, but I want
    # it to be as small as possible (and be able to read what the output
    # is while debugging).
    if text is not None:
        text_part = MIMEText(text, 'plain')
        text_part.set_charset('utf8')
        mail.attach(text_part)
    if html is not None:
        html_part = MIMEText(html, 'html')
        html_part.set_charset('utf8')
        mail.attach(html_part)

    return (from_, to + cc + bcc, mail.as_string())


class Mailer(object):

    """Class for sending mail via SMTP.

    The constructor takes arguments for setting up the connection, and the
    send method takes arguments for building the message.

    The connection is setup automatically upon sending a message, and left
    open until the object is destroyed, or the close method is called. Once
    closed, a call to send will open up a new connection.

    """

    def __init__(self, host='localhost', port=25, username=None,
        password=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._smtp = None
        self._smtp_lock = RLock()

    def __del__(self):
        with self._smtp_lock:
            try:
                self.close()
            except AttributeError:
                pass

    def connect(self):
        """Connect to the SMTP server if there is no connection already.

        Returns silently if there is already an established connection.

        """
        with self._smtp_lock:
            if self._smtp:
                return
            smtp = smtplib.SMTP()
            smtp.connect(self.host, self.port)
            if self.username is not None:
                smtp.login(self.username, self.password)
            self._smtp = smtp

    def close(self):
        """Close the SMTP connection if it is setup.

        Does nothing if there is no connection.

        """
        with self._smtp_lock:
            self.smtp.quit()
            self.smtp = None

    def send(self, *args, **kwargs):
        """Build and sent a message.

        Arguments are all passed directly into `format_mail` to build the
        message.
        
        This returns whatever smtplib.SMTP.sendmail returns (a dict of errors
        which will be empty if everything went okay). However, it is likely
        that the errors would be generated further into the chain of smtp
        servers, and we will never know about it.

        """
        from_, to, mail = format_mail(*args, **kwargs)
        with self._smtp_lock:
            self.connect()
            return self._smtp.sendmail(from_, to, mail)


def send(**kwargs):
    """Establish a connection and send a message in one stroke.

    Everything must be passed as keyword arguments. They will be routed as
    appropriate to either the constructor of a Mailer, or to the send method.

    """
    init_keys = set('host port username password'.split())
    init_kwargs = {}
    send_kwargs = {}
    for k, v in kwargs.iteritems():
        (init_kwargs if k in init_keys else send_kwargs)[k] = v
    mailer = Mailer(**init_kwargs)
    mailer.send(**send_kwargs)


if __name__ == '__main__':

    import nose; nose.run(defaultTest=__name__)
    exit()

    # Run the following in the console to see the output:
    #   python -m smtpd -n -c DebuggingServer localhost:1025

    print
    print "Sending..."
    mailer = Mailer('localhost')
    print mailer.send(
        from_=('Mike Boers', 'mail@example.com'),
        text='This is the text message.',
        html=u'<b>This</b> is the <i>html</i> message. ¡™£¢∞§¶•ªº',
        to=[('Mike Boers', 'mail@example.com')],
        subject='TESTING',
    )

    print 'Done.'
