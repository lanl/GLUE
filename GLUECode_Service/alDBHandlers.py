from glueCodeTypes import DatabaseMode

class ALDBHandle:
    """Abstract Base Class to Provide Interface to Databases

    Interface to databases used by glue code to allow for using
    different database providers depending on need of application
    """
    def __init__(self, dbConfig: dict, persistence: bool):
        """Constructor for ALDBHandle

        Args:
            dbConfig (dict): Configuration variables for run
            persistence (bool): Boolean to indicate if this should maintain a persistent database connection
        """
        self.dbURL = dbConfig["DatabaseURL"]
        self.persistence = persistence
        self.cursor = None
        self.handle = None
    def openCursor(self):
        """Reconnect to DB if needed and return cursor object

        Raises:
            Exception: Raises exception if not overriden through polymorphism
        """
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def execute(self, query: str, args: tuple=None):
        """Submit request to database

        Args:
            query (str): Query string formatted with args represented as '?'
            args (tuple, optional): _description_. Arguments to populate query string. Defaults to None.

        Raises:
            Exception: Raises exception if not overriden through polymorphism
        """
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeCursor(self):
        """Closes cursor and, if needed, disconnects fromn DB

        Raises:
            Exception: Raises exception if not overriden through polymorphism
        """
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def commit(self):
        """Calls commit/finalize/fence command for writes to databases

        Raises:
            Exception: Raises exception if not overriden through polymorphism
        """
        raise Exception("Use of Abstract Base Class for ALDBHandle")
    def closeDB(self):
        """Disconnects from database

        Raises:
            Exception: Raises exception if not overriden through polymorphism
        """
        raise Exception("Use of Abstract Base Class for ALDBHandle")

class SQLiteHandle(ALDBHandle):
    """Implementation of ALDBHandle for SQLite
    """
    def __init__(self, dbConfig, persistence):
        """Constructor for SQLiteHandle

        Args:
            dbConfig (dict): Configuration variables for run
            persistence (bool): Boolean to indicate if this should maintain a persistent database connection
        """
        # Call parent constructor
        ALDBHandle.__init__(self, dbConfig, persistence)
        # And import headers for later
        import sqlite3
    def openCursor(self):
        """Reconnect to SQLite if needed and return cursor object

        Returns:
            Cursor object to write directly to SQLite DB
        """
        # Hopefully duplicate import mostly for linting purposes
        import sqlite3
        #Always try/except as we may have closed the DB
        try:
            self.cursor = self.handle.cursor()
        except Exception as ex:
            self.handle = sqlite3.connect(self.dbURL, timeout=45.0)
            self.cursor = self.handle.cursor()
        return self.cursor
    def execute(self, query, args=None):
        """Submit query to SQLite database

        Args:
            query (str): Query string formatted with args represented as '?'
            args (tuple, optional): _description_. Arguments to populate query string. Defaults to None.

        Returns:
            Returns result of query for error checking
        """
        procQuery = query
        if args is None:
            return self.cursor.execute(procQuery)
        else:
            return self.cursor.execute(procQuery, args)
    def closeCursor(self):
        """Closes cursor to SQLite database and DB itself if not persistent
        """
        self.cursor.close()
        if not self.persistence:
            self.handle.close()
    def commit(self):
        """Call commit/fence on SQLite database
        """
        self.handle.commit()
    def closeDB(self):
        """Close SQLite database
        """
        self.handle.close()

def getDBHandle(dbConfigDict, persistence=False):
    """Factory to provide desired DBHandle implementation

    Args:
        dbConfig (dict): Configuration variables for run
            persistence (bool): Boolean to indicate if this should maintain a persistent database connection

    Raises:
        Exception: If unsupported database type is selected

    Returns:
        An object implementing the ALDBHandle abstract base class for the specified database backend
    """
    dbHandle = None
    if dbConfigDict["DatabaseMode"] == DatabaseMode.SQLITE:
        dbHandle = SQLiteHandle(dbConfigDict, persistence)
    elif dbConfigDict["DatabaseMode"] == DatabaseMode.MYSQL:
        #TODO: Implement MySQL logic
        raise Exception('Using Unsupported Database Type')
    else:
        raise Exception('Using Unsupported Database Type')
    return dbHandle
