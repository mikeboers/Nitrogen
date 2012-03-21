
from .app import Core
from .auth import AuthAppMixin
from .crud import CRUDAppMixin
from .exception import ExceptionAppMixin
from .forms import FormAppMixin
from .imgsizer import ImgSizerAppMixin
# from .js import JavaScriptAppMixin
from .logs import LoggingAppMixin
from .session import SessionAppMixin
from .sqlalchemy.app import SQLAlchemyAppMixin
# from .textblobs import TextBlobAppMixin
from .tracker import TrackerAppMixin
from .view.app import ViewAppMixin
from .cookies import CookieAppMixin

__all__ = ['App']

# Be careful about the order of these.
class App(
    ImgSizerAppMixin, # Needs View
    # TextBlobAppMixin, # Needs Form and CRUD.
    FormAppMixin, # Needs View
    CRUDAppMixin, # Needs View and SQLAlchemy
    TrackerAppMixin, # Needs View (and maybe session)
    SessionAppMixin, # Needs View (for view_globals)
    ViewAppMixin,
    SQLAlchemyAppMixin,
    AuthAppMixin,
    CookieAppMixin,
    LoggingAppMixin,
    ExceptionAppMixin, # Must be after anything that may throw exceptions.
    Core
):
    pass

