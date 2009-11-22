
import beaker.middleware

def session_wrapper(app, auto=True, secret='secret', data_dir='/tmp'):
    session_opts = {
        'session.key': 'session',
        'session.secret': secret,
        'session.data_dir': data_dir,
        'session.lock_dir': data_dir,
        'session.type': 'file',
        'session.auto': auto,
    }
    return beaker.middleware.SessionMiddleware(app, session_opts)

