# encoding: utf8

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging
from threading import Thread

def sendmail(text=None, html=None, async=False, **kwargs):
    
    if isinstance(text, unicode):
        text = text.encode('utf8')
    elif text is not None:
        text = str(text)
        
    if isinstance(html, unicode):
        html = html.encode('utf8')
    elif html is not None:
        html = str(html)
    
    if text is None and html is None:
        raise ValueError('Must be given atleast one of text or html.')
    
    mail = MIMEMultipart('alternative')
    
    mail['Subject'] = kwargs['subject']
    mail['To'] = kwargs['to']
    mail['From'] = kwargs.get('from') or kwargs.get('from_')
    
    if text is not None:
        mail.attach(MIMEText(text, 'plain', 'UTF-8'))
    if html is not None:
        mail.attach(MIMEText(html, 'html', 'UTF-8'))
    
    def target():
        smtp = smtplib.SMTP()
        smtp.connect(kwargs['host'], kwargs.get('port'))
    
        if 'username' in kwargs:
            smtp.login(kwargs['username'], kwargs.get('password'))
    
        smtp.sendmail(
            mail['From'],
            mail['To'],
            mail.as_string()
        )
    
        smtp.close()
     
    if async:
        Thread(target=target).start()
        
    else:
        target()
    
    
    
if __name__ == '__main__':
    
    # Run the following in the console to see the output:
    #   python -m smtpd -n -c DebuggingServer localhost:1025
    
    print sendmail(
        text='This is the text message.',
        html=u'<b>This is the html message. ¡™£¢∞§¶•ªº</b>',
        host='localhost',
        port=1025,
        from_='a@example.com',
        to='b@example.com',
        subject='TESTING!',
        async=True
    )
    print 'back'
