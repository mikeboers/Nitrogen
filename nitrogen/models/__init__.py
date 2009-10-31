
import logging
logger = logging.getLogger('sqlalchemy')
logger.setLevel(logging.WARNING)

import meta

def setup_meta(engine):
    meta.Session.configure(bind=engine)
    meta.engine = engine







