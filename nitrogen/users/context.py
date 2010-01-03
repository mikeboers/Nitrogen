

from fnmatch import fnmatch
import os
import hashlib
import datetime

from sqlalchemy import *
from sqlalchemy.orm import mapper
from sqlalchemy.types import MutableType, TypeDecorator

from nitrogen.crypto.password import PasswordHash
from nitrogen.uri import Query
from nitrogen.model.context import ModelContext
from nitrogen.route.rerouter import ReRouter


class PasswordType(TypeDecorator):
    
    impl = String
    
    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return PasswordHash(value) if value else PasswordHash()
    
    def copy(self):
        return PasswordType()
    
    def copy_value(self, value):
        return PasswordHash(str(value) if value is not None else None)
    
    def is_mutable(self):
        return True
        
    
class UserContext(object):
    
    def __init__(self, name, model_context):
        self.name = str(name)
        self.model_context = model_context
        self.session = self.model_context.local_session()
        self._build_user_table()
        self._build_user_model()
        self._setup_user_mapping()
    
    def __getattr__(self, name):
        if hasattr(self.model_context, name):
            return getattr(self.model_context, name)
        raise AttributeError(name)
    
    def _build_user_table(self):
        self.user_table = Table('%s-users' % self.name, self.model_context.metadata,
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
        
    
def test_stuff():
    model_context = ModelContext('sqlite:///:memory:')
    user_context = UserContext('main', model_context)
    
    model_context.create_tables()
    
    print user_context
    print user_context.user_table
    print user_context.User
    
    mike = user_context.User(email='test@example.com')
    tanya = user_context.User(email='test@tanyastemberger.com')
    
    s = user_context.session
    s.add(mike)
    s.add(tanya)
    s.commit()
    
    print s.query(user_context.User).all()
    
    
if __name__ == '__main__':
    from ..test import run
    run()
    
