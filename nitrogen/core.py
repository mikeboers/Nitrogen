
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
from .auth import AuthAppMixin

__all__ = ['App']

# Be careful about the order of these.
class App(
    ImgSizerAppMixin, # Needs View
    TextBlobAppMixin, # Needs Form and CRUD.
    FormAppMixin, # Needs View
    CRUDAppMixin, # Needs View and SQLAlchemy
    SessionAppMixin, # Needs View (for view_globals)
    ViewAppMixin,
    SQLAlchemyAppMixin,
    AuthAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin, # Must be after anything that may throw exceptions.
    Core
):
    pass

