from . import *


@route('/')
def do_index(request):
    if request.user_id:
        return Response('logged in as %s' % request.user_id)
    else:
        return Response('not logged in')

@route('/login', defaults={'user': 'default'})
@route('/login/{user}')
def do_login(request):
    user = request.route['user']
    # Verify their credentials here.
    response = Response()
    response.login(user)
    response.redirect('/auth')
    return response

@route('/logout')
def do_logout(request):
    response = Response()
    response.logout()
    response.redirect('/auth')
    return response
