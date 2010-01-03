

from fnmatch import fnmatch
import os
import hashlib
import datetime

from sqlalchemy import *
from sqlalchemy.orm import mapper
from sqlalchemy.types import MutableType, TypeDecorator

from nitrogen.crypto import timed_hash
from nitrogen.crypto.password import PasswordHash
from nitrogen.uri import Query
from nitrogen.model.environ import ModelEnviron
from nitrogen.route.rerouter import ReRouter

from . import *
   


# class PermissionType(MutableType, TypeDecorator):
#     impl = Unicode
#     def process_bind_param(self, value, dialect):
#         return u','.join(value) if value is not None else None
#     def process_result_value(self, value, dialect):
#         return value.split(',') if value is not None else None
#     def copy_value(self, value):
#         return value[:]


class PasswordType(TypeDecorator):
    
    impl = String
    
    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return PasswordHash(value) if value else PasswordHash()
    
    def copy(self):
        return PasswordType()
    
    def copy_value(self, value):
        return PasswordHash(str(value or ''))
    
    def is_mutable(self):
        return True
    


def build_User(name, model_environ):
    class User(model_environ.Base):
        __tablename__ = '%s-users' % name

        id = Column(Integer, primary_key=True)
        
        email = Column(Unicode, unique=True)
        email_is_verified = Column(Boolean, default=False)
        
        password_hash = Column(String)
        
        is_superuser = Column(Boolean, default=False)
        is_active = Column(Boolean, default=True)
        
        @property
        def is_anonymous(self):
            return False
        
        def __init__(self, **kwargs):
            super(User, self).__init__(**kwargs)
            self.is_authenticated = False
        
        def __repr__(self):
            return '<User:%r>' % (self.email)



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
    
    def __init__(self, name, model_environ, view_environ=None):
        self.name = str(name)
        self.model_environ = model_environ
        self.view_environ = view_environ
        self.session = self.model_environ.local_session()
        self._build_user_table()
        self._build_user_model()
        self._setup_user_mapping()
        self._setup_router()
    
    def _build_user_table(self):
        self.user_table = Table('%s-users' % self.name, self.model_environ.metadata,
            Column('id', Integer, primary_key=True),
            Column('email', Unicode, unique=True),
            Column('email_is_verified', Boolean, default=False),
            Column('password_hash', PasswordType),
            Column('is_superuser', Boolean, default=False),
            Column('is_active', Boolean, default=True),
        )
    
    def _build_user_model(self):
        class User(object):
            
            def __init__(self, email, password=None):
                self.email = email
                self._password_hash = PasswordHash()
                if password is not None:
                    self.password.set(password)
                
            def __repr__(self):
                return '<%s:%r>' % (self.__class__.__name__, self.email)
            
            @property
            def password(self):
                return self._password_hash

        self.User = User
        
    def _setup_user_mapping(self):
        mapper(self.User, self.user_table, properties={
            '_password_hash': self.user_table.c.password_hash
        })
    
    def _setup_router(self):
        self.router = ReRouter()
    
    def __call__(self, *args, **kwargs):
        return self.router(*args, **kwargs)
        
    
def test_stuff():
    model_environ = ModelEnviron('sqlite:///:memory:')
    user_environ = UserEnviron('main', model_environ)
    
    model_environ.create_tables()
    
    print user_environ
    print user_environ.user_table
    print user_environ.User
    
    mike = user_environ.User(email='test@example.com')
    tanya = user_environ.User(email='test@tanyastemberger.com')
    
    s = user_environ.session
    s.add(mike)
    s.add(tanya)
    s.commit()
    
    print s.query(user_environ.User).all()
    
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
    
    
