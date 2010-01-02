

from fnmatch import fnmatch
import os
import hashlib
import datetime

from sqlalchemy import *

from nitrogen.crypto import timed_hash
from nitrogen.uri import Query

from . import *
   


# class PermissionType(MutableType, TypeDecorator):
#     impl = Unicode
#     def process_bind_param(self, value, dialect):
#         return u','.join(value) if value is not None else None
#     def process_result_value(self, value, dialect):
#         return value.split(',') if value is not None else None
#     def copy_value(self, value):
#         return value[:]


class Password(object):
    def __init__(self, user):
        self.user = user
    def __eq__(self, password):
        hash = str(self.user._password_hash).decode('hex')
        return hash == timed_hash(password, hash)
    def __repr__(self):
        return '<Password:%s>' % self.user._password_hash


def build_User(name, model_environ):
    class User(model_environ.Base):
        __tablename__ = '%s-users' % name

        id = Column(Integer, primary_key=True)
        
        name = Column(Unicode, unique=True)
        real_name = Column(Unicode)
        
        email = Column(Unicode, unique=True)
        email_is_verified = Column(Boolean, default=False)
        
        password_hash = Column(String)
        
        date_created = Column(DateTime, default=datetime.datetime.now)
        last_login = Column(DateTime)
        
        is_superuser = Column(Boolean, default=False)
        is_active = Column(Boolean, default=True)
        
        @property
        def is_anonymous(self):
            return False
        
        def __init__(self, **kwargs):
            super(User, self).__init__(**kwargs)
            self.is_authenticated = False
        
        def __repr__(self):
            return '<User:%r:%r>' % (self.name, self.email)

        def set_password(self, password):
            self._password_hash = timed_hash(password).encode('hex')

        def check_password(self, password):
            try:
                hash = str(self._password_hash).decode('hex')
            except:
                hash = ''
            return hash == timed_hash(password, hash)

        @staticmethod
        def get_user_from_password_token(token):
            try:
                query = Query(token)
                id_ = int(query['u'])
                user = session.query(User).get(id_)
                if user.check_password_token(token):
                    return user
            except Exception as e:
                logging.exception('Error while processing token. %r' % e)

        def build_password_token(self):
            query = Query()
            query['u'] = self.id
            query['h'] = hashlib.md5(str(self.email + str(self._password_hash))).hexdigest()[:16]
            query.sign(config.crypto_entropy, max_age=60 * 60 * 24 * 7)
            return str(query)

        def check_password_token(self, token):
            query = Query(token)
            if not query.verify(config.crypto_entropy):
                return False
            if not query.get('h') == hashlib.md5(str(self.email + str(self._password_hash))).hexdigest()[:16]:
                return False
            return True
    return User
    
    
class UserEnviron(object):
    
    def __init__(self, name, model_environ):
        self.name = str(name)
        self.model_environ = model_environ
        
        self.User = build_User(name, model_environ)


        
    

if __name__ == '__main__':
    
    
    import sys
    sys.path.insert(0, '..')
    from nitrogen.test import run
    run()
    
    exit()
    
    for user in session.query(User):
        user.delete()
    session.commit()
    
    for email, password, perms, tier in [
        ('dev@example.com', 'password', ['*'], 0),
        ('sh@nemart.in', 'password', ['*'], 0),
    ]:
        
        user = User(email=email, password=password if password is not None else os.urandom(100), tier=tier, verified=password is not None)
        user._permissions = perms
        session.add(user)
    
    session.commit()
    
    query = user.build_password_token()
    print query, user.check_password_token(query)
    
    
