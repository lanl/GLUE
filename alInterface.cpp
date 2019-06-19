#include "alInterface.hpp"

#include <stdio.h>
#include <sqlite3.h> 

///TODO: Verify this is the correct way to do a global variable
AsyncSelectTable_t nastyGlobalSelectTable;

static int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName) {
	return 0;
}

void buildTables(sqlite3 * dbHandle)
{
	char * createTable = "CREATE TABLE REQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, DENSITY REAL);";
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, createTable, dummyCallback, 0, &zErrMsg);
	if( sqlRet != SQLITE_OK )
	{
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
	}

	return;
}

void writeRequest(double density, int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO REQS VALUES(\'%s\', %d, %d, %f)", tag, mpiRank, reqNum, density);
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
	if( sqlRet != SQLITE_OK )
	{
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
	}
	return;
}

void readRequest(int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum, <TODO: Pointer to resultStruct>)
{
	return;
}

ResultStruct_t reqFineGrainSim(double density, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;

	ResultStruct_t retVal;

	///COMMENT: Changing to SQLite
	///  It provides a file-based DB. It has C, Python, and Klepto interfaces. As of sqlite3 it is probably somewhat
	///    performant with many concurrent writes and queries. And it will provide an easily queried DB for
	///    further study of the results to learn how to make our learners better
	///  Evidently the rest of the world has been right for 30-ish(?) years!
	///TABLE: (tag TEXT, rank INT, req INT, <inputs> REAL)

	//Send request
	writeRequest(density, mpiRank, tag, dbHandle, reqNumber);

	//Spin on file until result is available
	int haveResult = 0;
	while(!haveResult)
	{
		///TODO: Add in readRequest and spin on lock
		///COMMENT: CHanging to CXX in the hopes of a more portable thread/STL interface
	}

	//Increment request number
	reqNumber++;

	return retVal;
}