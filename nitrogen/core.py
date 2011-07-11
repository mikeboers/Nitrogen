
from .app import Core
from .sqlalchemy.app import SQLAlchemyAppMixin
from .exception import ExceptionAppMixin
from .forms import FormAppMixin
from .imgsizer import ImgSizerAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .textblobs import TextBlobAppMixin
from .view.app import ViewAppMixin
from .crud import CRUDAppMixin

__all__ = ['App']

# Be careful about the order of these.
class App(
    ImgSizerAppMixin, # Must be before View
    TextBlobAppMixin, # Must be before Form and CRUD.
    FormAppMixin, # Must be before View
    CRUDAppMixin, # Must be before View and DB
    ViewAppMixin,
    SessionAppMixin,
    SQLAlchemyAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin, # Must be after anything that may throw exceptions.
    Core
):
    pass

