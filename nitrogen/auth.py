import logging
from urllib import urlencode

from webstar.core import RouteStep

from .request import Request, Response
from . import status


log = logging.getLogger(__name__)


Allow = True
Deny = False
Everyone = '*'
AllPermissions = '*'


# Decorator to attach ACLs to functions.
def ACL(*acl):
    def _ACL(func):
        func.__dict__.setdefault('__acl__', []).extend(acl)
        return func
    return _ACL


def get_route_acl(route):
    acl = []
    for step in reversed(route):
        acl.extend(step.head.__dict__.get('__acl__', []))
    acl.extend(route[0].router.__dict__.get('__acl__', []))
    return acl


class AuthAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(AuthAppMixin, self).__init__(*args, **kwargs)
        self.router.predicates.append(self.route_acl_predicate)
        self.router.__acl__ = [
            (Allow, Everyone, 'view'),
        ]
    
    def setup_config(self):
        super(AuthAppMixin, self).setup_config()
        self.config.setdefaults(
            auth_login_url='/login',
            auth_cookie_name='user_id',
        )
        
    def route_acl_predicate(self, route):
        for ace in get_route_acl(route):
            log.info('ACE: %r' % (ace, ))
            if not ace[0]:
                route.append(RouteStep(
                    head=self.authn_required_app,
                    router=self
                ))
        return True
    
    @Request.application
    def authn_required_app(self, request):
        return status.SeeOther(self.config.auth_login_url + '?' + urlencode(dict(
            redirect=request.url,
        )))
    
    class RequestMixin(object):
        
        @property
        def user_id(self):
            return self.cookies.get(self.app.config.auth_cookie_name)
    
    class ResponseMixin(object):
        
        def login(self, user_id):
            self.cookies[self.app.config.auth_cookie_name] = user_id
        
        def logout(self):
            self.cookies.expire(self.app.config.auth_cookie_name)
    