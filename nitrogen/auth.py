import logging
from urllib import urlencode

import werkzeug.utils
import werkzeug as wz
from webstar.core import RouteStep

from .request import Request, Response
from . import status


log = logging.getLogger(__name__)




# Decorator to attach ACLs to functions.
def ACL(*acl):
    def _ACL(func):
        func.__dict__.setdefault('__acl__', []).extend(acl)
        return func
    return _ACL


def get_route_acl(route):
    acl = []
    for step in reversed(route):
        # The router or final app.
        acl.extend(getattr(step.head, '__acl__', []))
        # In the route data.
        acl.extend(step.data.get('__acl__', []))
        # In __acl__ on the module if from register_module.
        acl.extend(getattr(step.data.get('__module__', None), '__acl__', []))
    return acl


def has_permission(request, acl, permission):
    for state, predicate, permissions in acl:
        predicate = parse_predicate(predicate)
        if predicate(request):
            if permission in parse_permissions(permissions):
                log.info('ACE matched: %s%r via %r' % ('' if state else 'not ', permission, predicate))
                return state
    return False



class AuthAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(AuthAppMixin, self).__init__(*args, **kwargs)
        self.router.predicates.append(self.route_acl_predicate)
        self.router.__acl__ = [
            (True , '__any__', 'view'),
            (False, '__any__', '__all__'),
        ]
    
    def setup_config(self):
        super(AuthAppMixin, self).setup_config()
        self.config.setdefaults(
            auth_login_url='/login',
            auth_cookie_name='user_id',
        )
        
    def route_acl_predicate(self, route):
        if not has_permission(self._local.request, get_route_acl(route), 'view'):
            if self._local.request.user_id is None:
                route.step(self.authn_required_app, router=self)
            else:
                route.step(self.authz_denied_app, router=self)
        return True
    
    @Request.application
    def authn_required_app(self, request):
        return status.SeeOther(self.config.auth_login_url + '?' + urlencode(dict(
            redirect=request.url,
        )))
    
    @Request.application
    def authz_denied_app(self, request):
        raise status.Forbidden()
    
    class RequestMixin(object):
        
        @property
        def user_id(self):
            return self.cookies.get(self.app.config.auth_cookie_name)
        
        @wz.utils.cached_property
        def user_principals(self):
            principals = set()
            if self.user_id is not None:
                principals.add(self.user_id)
            return principals
        
        def has_permission(self, permission):
            return has_permission(self, get_route_acl(self.route_steps), permission)
            
    
    class ResponseMixin(object):
        
        def login(self, user_id):
            self.cookies[self.app.config.auth_cookie_name] = user_id
        
        def logout(self):
            self.cookies.expire(self.app.config.auth_cookie_name)






# predicates

class Any(object):
    def __call__(self, request):
        return True
    def __repr__(self):
        return 'auth.Any()'

class Not(object):
    def __init__(self, predicate):
        self.predicate = predicate
    def __call__(self, request):
        return not self.predicate(request)
    def __repr__(self):
        return 'auth.Not(%r)' % self.predicate

class And(object):
    op = all
    def __init__(self, *predicates):
        self.predicates = predicates
    def __call__(self, request):
        return self.op(x(request) for x in self.predicates)
    def __repr__(self):
        return 'auth.%s(%s)' % (self.op.__name__, ', '.join(repr(x) for x in self.predicates))

class Or(And):
    op = any

class Principal(object):
    def __init__(self, principal):
        self.principal = principal
    def __call__(self, request):
        return self.principal in request.user_principals
    def __repr__(self):
        return 'auth.Principal(%r)' % self.principal

class Authenticated(object):
    def __call__(self, request):
        return request.user_id is not None
    def __repr__(self):
        return 'auth.%s()' % self.__class__.__name__

NotAnonymous = Authenticated
Anonymous = lambda: Not(Authenticated())

class Local(object):
    def is_met(self, request):
        return request.remote_addr in ('127.0.0.1', '::0')
    def __repr__(self):
        return 'auth.Local()'

Remote = lambda: Not(Local())


string_predicates = {
    '__anonymous__': Anonymous(),
    '__authenticated__': Authenticated(),
    '__local__': Local(),
    '__remote__': Remote(),
    '__any__': Any(),
    '*': Any(),
}

def parse_predicate(input):
    
    if isinstance(input, basestring):
        negate = input.startswith('!')
        if negate:
            input = input[1:]
        predicate = string_predicates.get(input) or Principal(input)
        if negate:
            predicate = Not(predicate)
        return predicate
    
    if isinstance(input, (tuple, list)):
        return And(parse_predicate(x) for x in input)
    
    return input



class AllPermissions(object):
    def __contains__(self, other):
        return True
        
string_permissions = {
    '__all__': AllPermissions(),
    '*': AllPermissions(),
}

def parse_permissions(input):
    if isinstance(input, basestring):
        if input in string_permissions:
            return string_permissions[input]
        return set([input])
    return input


