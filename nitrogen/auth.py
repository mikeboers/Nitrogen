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
        func.__dict__.setdefault('__acl__', []).extend(parse_ace(x) for x in acl)
        return func
    return _ACL

def requires(*predicates):
    def _requires(func):
        func.__dict__.setdefault('__auth_predicates__', []).extend(parse_predicate(x) for x in predicates)
        return func
    return _requires


def get_route_prop_list(route, name):
    acl = []
    for step in reversed(route):
        # The router or final app.
        acl.extend(getattr(step.head, name, []))
        # In the route data.
        acl.extend(step.data.get(name, []))
        # In __acl__ on the module if from register_module.
        acl.extend(getattr(step.data.get('__module__', None), name, []))
    return acl

get_route_acl = lambda route: get_route_prop_list(route, '__acl__')
get_route_predicates = lambda route: get_route_prop_list(route, '__auth_predicates__')


def check_acl_for_permission(request, acl, permission):
    for state, predicate, permissions in acl:
        predicate = parse_predicate(predicate)
        if predicate(request):
            if permission in parse_permissions(permissions):
                log.debug('ACE matched: %s%r via %r' % ('' if state else 'not ', permission, predicate))
                return state
    return False


            

class AuthAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(AuthAppMixin, self).__init__(*args, **kwargs)
        
        # Default ACL list that will be checked by an auth_predicate.
        self.router.__acl__ = [
            (True , '__any__', 'route'),
            (False, '__any__', '__all__'),
        ]
        
        # Here is the auth predicate that actually checks ACLs
        self.router.__auth_predicates__ = [HasPermission('route')]
    
    def setup_config(self):
        super(AuthAppMixin, self).setup_config()
        self.config.setdefaults(
            auth_login_url='/login',
            auth_cookie_name='user_id',
        )
        
    def _get_wsgi_app(self, environ):
        app = super(AuthAppMixin, self)._get_wsgi_app(environ)
        request = self.Request(environ)
        route = request.route_steps
        # We always have a route at this point if the route was successful.
        # We may not have one if it is doing a normalization redirection or
        # if a route was not found
        if route:
            for predicate in get_route_predicates(request.route_steps):
                if not predicate(request):
                    if request.user_id is None:
                        return self.authn_required_app
                    else:
                        return self.authz_denied_app
        return app
    
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
            return check_acl_for_permission(self, get_route_acl(self.route_steps), permission)
            
    
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
    def __call__(self, request):
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


# More general predicate.
class HasPermission(object):
    def __init__(self, permission):
        self.permission = permission
    def __call__(self, request):
        return request.has_permission(self.permission)
        

# Permissions
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

def parse_ace(ace):
    state, predicate, permissions = ace
    return state, parse_predicate(predicate), parse_permissions(permissions)


