
from .app import Core
from .db.app import DBAppMixin
from .exception import ExceptionAppMixin
from .imgsizer import ImgSizerAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .view.app import ViewAppMixin

# Be careful about the order of these.
class App(
    ImgSizerAppMixin, # Must be before View
    ViewAppMixin,
    SessionAppMixin,
    DBAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin,
    Core
):
    pass

del Core
del DBAppMixin
del ExceptionAppMixin
del ImgSizerAppMixin
del LoggingAppMixin
del SessionAppMixin
del ViewAppMixin

from .route import ReRouter
from .status import abort, redirect