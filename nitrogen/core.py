
from .db.app import DBAppMixin
from .view.app import ViewAppMixin
from .error import ErrorAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin

class App(DBAppMixin, ViewAppMixin, ErrorAppMixin, LoggingAppMixin, SessionAppMixin):
    pass

del DBAppMixin
del ViewAppMixin
del ErrorAppMixin
del LoggingAppMixin
del SessionAppMixin


from .route import ReRouter