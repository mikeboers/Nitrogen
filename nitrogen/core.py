
from .app import Core
from .db.app import DBAppMixin
from .exception import ExceptionAppMixin
from .forms import FormAppMixin
from .imgsizer import ImgSizerAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .textblobs import TextBlobAppMixin
from .view.app import ViewAppMixin
from .crud import CRUDAppMixin

# Be careful about the order of these.
class App(
    ImgSizerAppMixin, # Must be before View
    TextBlobAppMixin, # Must be before Form and CRUD.
    FormAppMixin, # Must be before View
    CRUDAppMixin, # Must be before View and DB
    ViewAppMixin,
    SessionAppMixin,
    DBAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin, # Must be after anything that may throw exceptions.
    Core
):
    pass

del Core
del DBAppMixin
del ExceptionAppMixin
del FormAppMixin
del ImgSizerAppMixin
del LoggingAppMixin
del SessionAppMixin
del TextBlobAppMixin
del ViewAppMixin

