"""Flickr API binding!"""

import urllib
import json
import hashlib
import pprint

REST_URL     = 'http://api.flickr.com/services/rest/';
AUTH_URL     = 'http://flickr.com/services/auth/';

PERMS_NONE   = 'none';
PERMS_READ   = 'read';
PERMS_WRITE  = 'write';
PERMS_DELETE = 'delete';

UPLOAD_URL   = 'http://api.flickr.com/services/upload/';
REPLACE_URL  = 'http://api.flickr.com/services/replace/';

class Error(ValueError):
    pass

class Flickr(object):
    
    def __init__(self, key, secret, token=None):
        self.key = key
        self.secret = secret
        self.token = token
        
        self.frob = None
        self._last_checked_token = None
        self._user = None
    
    def _sign_data(self, data):
        data['api_key'] = self.key
        to_sign = self.secret + ''.join('%s%s' % i for i in sorted(data.items()))
        data['api_sig'] = hashlib.md5(to_sign).hexdigest()
            
    def call(self, method, **data):
        data.update({
            'method': 'flickr.%s' % method,
            'format': 'json',
            'nojsoncallback': '1'
        })
        
        # Do auth if we have a user auth token.
        if self.token is not None:
            data['auth_token'] = self.token
        
        # Sign everyyhing!
        self._sign_data(data)
        
        url = REST_URL + '?' + urllib.urlencode(data)
        res = json.loads(urllib.urlopen(url).read())
        if res['stat'] == 'fail':
            raise Error(res['message'], res['code'])
        return res
    
    def build_web_auth_link(self, perms=PERMS_READ):
        """Build a link to authorize a web user.
        
        Upon authorization, the user will be returned to the callback-URL as
        define in the Flickr API setup at
        http://www.flickr.com/services/api/keys/ along with a GET frob
        parameter.
        
        Flickr docs are here:
            http://www.flickr.com/services/api/auth.howto.web.html
        """
        
        data = {'perms': perms}
        self._sign_data(data)
        return AUTH_URL + '?' + urllib.urlencode(data)
    
    def get_frob(self):
        """Retrieve a one-time use frob from Flickr server.
        
        Remembers the last retrieved frob for use in authenticating.
        
        For use when authenticating using desktop-app method.
        See: http://www.flickr.com/services/api/auth.howto.desktop.html
        """
        
        res = self.call('auth.getFrob')
        self.frob = res['frob']['_content']
        return self.frob
            
    def build_desktop_auth_link(self, perms=PERMS_READ, frob=None):
        """Build a link to authorize a desktop user.
        
        Accepts a frob, or automatically generates one and stores it at
        flickr.frob.
        
        See: http://www.flickr.com/services/api/auth.howto.desktop.html
        """
        
        data = {'perms': perms, 'frob': frob or self.get_frob()}
        self._sign_data(data)
        return AUTH_URL + '?' + urllib.urlencode(data)
    
    def get_token(self, frob=None):
        """Convert a (supposedly) authenticated frob into a user auth token.
        
        Will use flickr.frob if one is not supplied.
        
        This method only returns the token. The API call does return a lot
        more data, however. If you want the username, fullname, nsid, etc, you
        should make the API call yourself by:
            
            res = flickr.call('auth.getToken', frob=frob)
            token = res['token']['_content']
        
        Or use the flickr.authorize() method.
        
        See: http://www.flickr.com/services/api/auth.howto.web.html
        See: http://www.flickr.com/services/api/auth.howto.desktop.html
        See: http://www.flickr.com/services/api/flickr.auth.getToken.html
        """
        
        if not frob or self.frob:
            raise ValueError('No frob availible.')
        res = self.call('auth.getToken', frob=frob or self.frob)
        return res['auth']['token']['_content']
    
    def authorize(self, frob=None):
        """Authorize the instance after the user has shaken hands with Flickr.
        Returns the token.
        
        Uses the last retrieved frob if one is not supplied. Automatically
        remembers the token and user info.
        
        See: http://www.flickr.com/services/api/auth.howto.web.html
        See: http://www.flickr.com/services/api/auth.howto.desktop.html
        """
        
        if not frob or self.frob:
            raise ValueError('No frob availible.')
        
        res = self.call('auth.getToken', frob=frob or self.frob)
        self.token = res['auth']['token']['_content']
        self._last_checked_token = self.token
        self._user = res['auth']['user']
        
        return self.token
    
    def _assert_user_properties(self):
        if self.token is None:
            raise ValueError('Token is not set.')
        if self._last_checked_token != self.token:
            res = self.call('auth.checkToken', auth_token=self.token)
            self._user = res['auth']['user']
            self._last_checked_token = self.token
    
    @property
    def username(self):
        self._assert_user_properties()
        return self._user['username']
        
    @property
    def fullname(self):
        self._assert_user_properties()
        return self._user['fullname']
                    
    @property
    def nsid(self):
        self._assert_user_properties()
        return self._user['nsid']       
        

if __name__ == '__main__':
    
    nsid = '24585471@N05'
    flickr = Flickr('455486bdcbef56f033eb6b1fa9c06904', '0f5b3c7c71e21d5e')
    
    # res = flickr.call('photosets.getList', user_id=nsid)
    
    frob = '72157619404120930-92b4aa1e4a556a96-340372' or flickr.get_frob()
    print 'frob    :', frob
    # print flickr.build_desktop_auth_link(frob=frob)
    token = '72157619403956088-e74622cbe4505b9f' or flickr.get_token(frob)
    print 'token   :', token
    
    flickr.token = token
    print 'username:', flickr.username
    print 'fullname:', flickr.fullname
    print 'nsid    :', flickr.nsid