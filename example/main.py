from nitrogen.core import App

from . import config


# Create the app.
app = App(config.__dict__)

# Dump all app exports into the global namespace.
app.export_to(globals())

# Register our controllers.
# This needs to be done after the global export as the controllers may depend
# upon some of the values set.
app.router.register_module('/', __package__ + '.controllers._index') # Index.
app.router.register_package(None, __package__ + '.controllers', recursive=True)
