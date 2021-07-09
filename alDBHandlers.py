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
    def openCursor(self):
        import sqlite3
        self.handle = sqlite3.connect(self.dbURL, timeout=45.0)
        self.cursor = self.handle.cursor()
        return self.cursor
    def closeCursror(self):
        # TODO: Figure out a good way to handle persistence
        self.cursor.close()
        self.handle.close()
    def closeDB(self):
        pass

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
