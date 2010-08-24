
from .db.app import DBAppMixin
from .view.app import ViewAppMixin
from .error import ErrorAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin

# Be careful about the order of these.
class App(
    ViewAppMixin,
    SessionAppMixin,
    DBAppMixin,
    LoggingAppMixin,
    ErrorAppMixin
):
    pass

del DBAppMixin
del ViewAppMixin
del ErrorAppMixin
del LoggingAppMixin
del SessionAppMixin


from .route import ReRouter