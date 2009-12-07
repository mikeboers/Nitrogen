# encoding: utf8
"""

Wrapper around email and smtplib modules for the easy sending of mail.

If you want it asynchronous, use the threading module like so:
    from threading import Thread
    Thread(target=sendmail, kwargs=dict(...)).start()
    
TODO:
    - write a Sender class which opens a connection once, and sends lots of
      mail through it   
     
TESTING:
    python -m smtpd -n -c DebuggingServer localhost:1025

"""

from __future__ import absolute_import

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_7or8bit
from email.utils import parseaddr as _parse_addr, formataddr as _format_addr
from email.header import Header
import smtplib
from threading import RLock
import re
import string

def format_address(addr, strict=True):
    r"""
    
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
    if isinstance(addrs, basestring):
        addrs = [addrs]
    addrs = addrs or []
    return [format_address(x) for x in addrs]


class Mailer(object):
    
    def __init__(self, host=None, port=None, username=None, password=None):
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
        with self._smtp_lock:
            if self._smtp:
                return
            smtp = smtplib.SMTP()
            smtp.connect(self.host, self.port)
            if self.username is not None:
                smtp.login(self.username, self.password)
            self._smtp = smtp
    
    def close(self):
        with self._smtp_lock:
            self.smtp.quit()
            self.smtp = None
        
    def send(self, from_, to, subject, text=None, html=None, cc=None,
        bcc=None):
        
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
        
        from_ = format_address(from_)
        to = format_address_list(to)
        cc = format_address_list(cc)
        bcc = format_address_list(bcc)
        
        mail = MIMEMultipart('alternative')
        
        # Only encode the subject if we need to.
        if re.match('[ a-zA-Z0-9' + re.escape(string.punctuation) + ']*$', subject):
            mail['Subject'] = subject
        else:
            mail['Subject'] = Header(subject, 'utf8')
            
        mail['From'] = from_
        mail['To'] = ', '.join(to)
        if cc:
            mail['Cc'] = ', '.join(cc)
        
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
        
        with self._smtp_lock:
            self.connect()
            return self._smtp.sendmail(
                from_,
                to + cc + bcc,
                mail.as_string()
            )


def sendmail(**kwargs):
    init_keys = set('host port username password'.split())
    init_kwargs = {}
    send_kwargs = {}
    for k, v in kwargs.iteritems():
        (init_kwargs if k in init_keys else send_kwargs)[k] = v
    mailer = Mailer(**init_kwargs)
    mailer.send(**send_kwargs)

    
if __name__ == '__main__':
    
    from .test import run
    run()
    # exit()
    
    # Run the following in the console to see the output:
    #   python -m smtpd -n -c DebuggingServer localhost:1025
    
    print
    print "Sending..."
    mailer = Mailer(
        # host='localhost',
        # port=1025,
        
        host='localhost',
        port=587,
        username='johndoe',
        password='12345',
    )
    mailer.send(
        from_=(__name__ + ': TESTING', 'test@example.com'),
        text='This is the text message.',
        html=u'<b>This</b> is the <i>html</i> message. ¡™£¢∞§¶•ªº',
        to=[('Jim Bob', 'mail@example.com')],
        bcc='bcc@example.com',
        subject='TESTING',
    )
    
    print 'Done.'
