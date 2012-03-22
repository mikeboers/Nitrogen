from __future__ import absolute_import

from werkzeug import url_encode
from werkzeug import url_encode
from wtforms import ValidationError
from wtforms.fields import Field
import json
import urllib2


_ = lambda s: s
    

RECAPTCHA_API_SERVER = 'http://api.recaptcha.net/'
RECAPTCHA_SSL_API_SERVER = 'https://api-secure.recaptcha.net/'
RECAPTCHA_HTML = u'''
<script type="text/javascript">var RecaptchaOptions = %(options)s;</script>
<script type="text/javascript" src="%(script_url)s"></script>
<noscript>
  <div><iframe src="%(frame_url)s" height="300" width="500"></iframe></div>
  <div><textarea name="recaptcha_challenge_field" rows="3" cols="40"></textarea>
  <input type="hidden" name="recaptcha_response_field" value="manual_challenge"></div>
</noscript>
'''

RECAPTCHA_VERIFY_SERVER = 'http://api-verify.recaptcha.net/verify'



class RecaptchaWidget(object):

    def __init__(self, public_key, private_key, use_ssl=False, options=None):
        self.public_key = public_key
        self.private_key = private_key
        self.use_ssl = use_ssl
        self.options = options or {}

    def recaptcha_html(self, server, query, options):
        return RECAPTCHA_HTML % dict(
            script_url='%schallenge?%s' % (server, query),
            frame_url='%snoscript?%s' % (server, query),
            options=json.dumps(options)
        )

    def __call__(self, field, error=None, **kwargs):
        """Returns the recaptcha input HTML."""

        server = RECAPTCHA_SSL_API_SERVER if self.use_ssl else RECAPTCHA_API_SERVER
        query_options = dict(k=self.public_key)

        if getattr(field, 'recaptcha_error', None) is not None:
            query_options['error'] = unicode(field.recaptcha_error)

        query = url_encode(query_options)

        options = {
           'theme': 'clean',
            'custom_translations': {
                'visual_challenge':    _('Get a visual challenge'),
                'audio_challenge':     _('Get an audio challenge'),
                'refresh_btn':         _('Get a new challenge'),
                'instructions_visual': _('Type the two words:'),
                'instructions_audio':  _('Type what you hear:'),
                'help_btn':            _('Help'),
                'play_again':          _('Play sound again'),
                'cant_hear_this':      _('Download sound as MP3'),
                'incorrect_try_again': _('Incorrect. Try again.'),
            }
        }

        options.update(self.options)
        return self.recaptcha_html(server, query, options)


class RecaptchaField(Field):
    
    widget = None
    challenge = None
    private_key = None
    public_key=None
    use_ssl = False
    options = None
    
    # error message if recaptcha validation fails
    recaptcha_error = None

    def __init__(self, label='', validators=None, **kwargs):
        for name in 'public_key', 'private_key', 'use_ssl', 'options':
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
        self.widget = RecaptchaWidget(
            public_key=self.public_key,
            private_key=self.private_key,
            use_ssl=self.use_ssl,
            options=self.options or {}
        )
        validators = validators or [RecaptchaValidator()]
        super(RecaptchaField, self).__init__(label, validators, **kwargs)
    
    def remote_addr(self):
        raise RuntimeError('Must define remote_addr')
    
    def process(self, formdata, data=None):
        if formdata:
            self.challenge = formdata.getlist('recaptcha_challenge_field')[0]
            self.data = formdata.getlist('recaptcha_response_field')[0]
        
        
class RecaptchaValidator(object):
    """Validates a ReCaptcha."""
    
    _error_codes = {
        'invalid-site-public-key': 'The public key for reCAPTCHA is invalid',
        'invalid-site-private-key': 'The private key for reCAPTCHA is invalid',
        'invalid-referrer': 'The public key for reCAPTCHA is not valid for '
            'this domainin',
        'verify-params-incorrect': 'The parameters passed to reCAPTCHA '
            'verification are incorrect',
    }

    def __init__(self, message=u'Invalid words. Please try again.'):
        self.message = message

    def __call__(self, form, field):
        challenge = field.challenge
        response  = field.data
        remote_ip = field.remote_addr()

        if not challenge or not response:
            raise ValidationError('This field is required.')

        if not self._validate_recaptcha(field, challenge, response, remote_ip):
            field.recaptcha_error = 'incorrect-captcha-sol'
            raise ValidationError(self.message)

    def _validate_recaptcha(self, field, challenge, response, remote_addr):
        """Performs the actual validation."""

        private_key = field.private_key

        data = url_encode({
            'privatekey': private_key,
            'remoteip':   remote_addr,
            'challenge':  challenge,
            'response':   response
        })

        response = urllib2.urlopen(RECAPTCHA_VERIFY_SERVER, data)

        if response.code != 200:
            return False

        rv = [l.strip() for l in response.readlines()]

        if rv and rv[0] == 'true':
            return True

        if len(rv) > 1:
            error = rv[1]
            if error in self._error_codes:
                raise RuntimeError(self._error_codes[error])

        return False




