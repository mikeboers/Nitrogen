
from .db.app import DBAppMixin
from .error import ExceptionAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .view.app import ViewAppMixin

# Be careful about the order of these.
class App(
    ViewAppMixin,
    SessionAppMixin,
    DBAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin
):
    pass

del DBAppMixin
del ExceptionAppMixin
del LoggingAppMixin
del SessionAppMixin
del ViewAppMixin


from .route import ReRouter
from .status import abort, redirect