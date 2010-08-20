
from .db.app import DBAppMixin
from .view.app import ViewAppMixin
from .error import ErrorAppMixin
from .logs import LoggingAppMixin

class App(DBAppMixin, ViewAppMixin, ErrorAppMixin, LoggingAppMixin):
    pass

del DBAppMixin
del ViewAppMixin
del ErrorAppMixin
del LoggingAppMixin

from .route import ReRouter