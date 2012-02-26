from nitrogen import auth
from . import *


@route('/')
def do_index(request):
    if request.user_id:
        return Response('logged in as %s' % request.user_id, mimetype='text/plain')
    else:
        return Response('not logged in', mimetype='text/plain')

@route('/login')
def do_login(request):
    if request.method == 'POST':
        user = request.form['user']
        # Verify their credentials here.
        response = Response()
        response.login(user)
        response.redirect(request.args.get('redirect', '/auth'))
        return response
    else:
        return Response('''
            <form method="post">
                <input name="user" value="default"/><input type="submit" />
            </form>
        ''')

@route('/logout')
def do_logout(request):
    response = Response()
    response.logout()
    response.redirect('/auth')
    return response

@route('/protected')
@auth.requires(auth.Authenticated())
def do_protected(request):
    return Response('OK', mimetype='text/plain')

@route('/private')
@auth.requires(auth.Principal('root'))
def do_private(request):
    return Response('OK', mimetype='text/plain')

