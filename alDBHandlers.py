from glueCodeTypes import DatabaseMode

class ALDBHandle:
    def __init__(self, dbURL, persistence):
        self.dbURL = dbURL
        self.persistence = persistence
    def openCursor(self):
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeCursror(self):
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeDB(self):
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
    def closeCursror(self):
        self.cursor.close()
        if not self.persistence:
            self.handle.close()
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
