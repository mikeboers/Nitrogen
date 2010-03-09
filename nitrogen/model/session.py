from sqlalchemy.orm.session import Session as BaseSession


__all__ = ['Session']


class Session(BaseSession):
    
    """SQLAlchemy session class which adds primitive locking for SQLite.
    
    This is to be supplied to the 'class_' kwarg of the session_maker
    function. Please note that I haven't even bothered to see how to make this
    work with other backends. Maybe it is possible, maybe not.
    
    """    
    
    def lock(self, exclusive=False):
        """Lock the DB for our IMMEDIATE (default) or EXCLUSIVE use."""
        self.execute("BEGIN %S" % 'EXCLUSIVE' if exclusive else "IMMEDIATE")
    
    def write_lock(self):
        """Get an IMMEDIATE lock on the DB, so that noone but us may write."""
        self.lock(False)
    
    def read_lock(self):
        """Get an EXCLUSIVE lock on the DB, so that noone but us may read."""
        self.lock(True)