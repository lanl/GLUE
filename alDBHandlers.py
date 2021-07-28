from glueCodeTypes import DatabaseMode

class ALDBHandle:
    """Abstract Base Class to Provide Interface to Databases

    Interface to databases used by glue code to allow for using
    different database providers depending on need of application"""
    def __init__(self, dbURL: str, persistence: bool):
        self.dbURL = dbURL
        self.persistence = persistence
        self.cursror = None
        self.handle = None
    def openCursor(self):
        # Reconnects to DB if needed and returns cursor object
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def execute(self, query: str, args: tuple=None):
        # Takes query string and arguments tuple as input.
        #   Query string formatted with args represented as '?'
        #   Preprocesses as needed and returns result of execute()
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeCursror(self):
        # Closes cursror and, if needed, disconnects fromn DB
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def commitDB(self):
        # Calls commit command for writes
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeDB(self):
        # Disconnects from DB
        raise Exception("Use of Abstract Base Class for ALDBHandle")

class SQLiteHandle(ALDBHandle):
    def __init__(self, dbURL, persistence):
        # Call parent constructor
        ALDBHandle.__init__(self, dbURL, persistence)
        # And import headers for later
        import sqlite3
    def openCursor(self):
        # Hopefully duplicate import mostly for linting purposes
        import sqlite3
        #Always try/except as we may have closed the DB
        try:
            self.cursor = self.handle.cursor()
        except Exception as ex:
            self.handle = sqlite3.connect(self.dbURL, timeout=45.0)
            self.cursor = self.handle.cursor()
        return self.cursor
    def execute(self, query, args):
        procQuery = query
        #TODO: Test what happens if args is an empty tuple
        if args is None:
            return self.cursor.execute(procQuery)
        else:
            return self.cursor.execute(procQuery, args)
    def closeCursror(self):
        self.cursor.close()
        if not self.persistence:
            self.handle.close()
    def commit(self):
        self.handle.commit()
    def closeDB(self):
        self.handle.close()

def getDBHandle(dbURL, dbType, persistence=False):
    dbHandle = None
    if dbType == DatabaseMode.SQLITE:
        dbHandle = SQLiteHandle(dbURL, persistence)
    elif dbType == DatabaseMode.MYSQL:
        #TODO: Implement MySQL logic
        raise Exception('Using Unsupported Database Type')
    else:
        raise Exception('Using Unsupported Database Type')
    return dbHandle
