
from .db.app import DBAppMixin
from .exception import ExceptionAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .view.app import ViewAppMixin
from .app import Core

# Be careful about the order of these.
class App(
    ViewAppMixin,
    SessionAppMixin,
    DBAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin,
    Core
):
    pass

del DBAppMixin
del ExceptionAppMixin
del LoggingAppMixin
del SessionAppMixin
del ViewAppMixin
del Core

from .route import ReRouter
from .status import abort, redirect