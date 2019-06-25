#include "alInterface.hpp"

#include <cstdio>
#include <cstdlib>
#include <sqlite3.h> 

///TODO: Verify this is the correct way to do a global variable
AsyncSelectTable_t nastyGlobalSelectTable;

static int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName)
{
	//Do nothing. We don't need a result from this op
	return 0;
}

static int readCallback_single(void *NotUsed, int argc, char **argv, char **azColName)
{
	///TABLE: (tag TEXT, rank INT, req INT, <outputs> REAL)
	//Process row: Ignore 0 (tag) and 1 (rank)
	int reqID = atoi(argv[2]);
	SelectResult_t result;

	//Add results
	result.density = atof(argv[3]);

	nastyGlobalSelectTable.tableMutex.lock();
	nastyGlobalSelectTable.resultTable[reqID] = result;
	nastyGlobalSelectTable.tableMutex.unlock();	

	return 0;
}

void buildTables(sqlite3 * dbHandle)
{
	char * reqTable = "CREATE TABLE REQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, DENSITY REAL);";
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, reqTable, dummyCallback, 0, &zErrMsg);
	if( sqlRet != SQLITE_OK )
	{
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
		exit(1);
	}

	char * resTable = "CREATE TABLE RESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, DENSITY REAL);";
	sqlRet = sqlite3_exec(dbHandle, resTable, dummyCallback, 0, &zErrMsg);
	if( sqlRet != SQLITE_OK )
	{
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
		exit(1);
	}

	return;
}

void writeRequest(InputStruct_t input, int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO REQS VALUES(\'%s\', %d, %d, %f)", tag, mpiRank, reqNum, input.density);
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
	if( sqlRet != SQLITE_OK )
	{
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
		exit(1);
	}
	return;
}

ResultStruct_t reqFineGrainSim_single(InputStruct_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;

	ResultStruct_t retVal;

	char sqlBuf[2048];
	char *err = nullptr;

	///COMMENT: Changing to SQLite
	///  It provides a file-based DB. It has C, Python, and Klepto interfaces. As of sqlite3 it is probably somewhat
	///    performant with many concurrent writes and queries. And it will provide an easily queried DB for
	///    further study of the results to learn how to make our learners better
	///  Evidently the rest of the world has been right for 30-ish(?) years!
	///TABLE: (tag TEXT, rank INT, req INT, <inputs> REAL)

	//Send request
	writeRequest(input, mpiRank, tag, dbHandle, reqNumber);

	//Spin on file until result is available
	bool haveResult = false;
	while(!haveResult)
	{
		//Send SELECT with sqlite3_exec. Blocking?
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ=%d AND TAG=%s AND RANK=%d;", reqNumber, tag, mpiRank);
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
		if (rc != SQLITE_OK)
		{
			fprintf(stderr, "Error in reqFineGrainSim_single\n");
			fprintf(stderr, "SQL error: %s\n", err);

			sqlite3_free(err);
			sqlite3_close(dbHandle);
			exit(1);
		}

		//Get lock
		nastyGlobalSelectTable.tableMutex.lock();
		//Check if result in table
		auto res = nastyGlobalSelectTable.resultTable.find(reqNumber);
		if (res != nastyGlobalSelectTable.resultTable.end())
		{
			//It exists, so this is the final iteration of the loop
			haveResult = true;
			retVal = res->second;
		}
		//Relase lock
		nastyGlobalSelectTable.tableMutex.unlock();	
	}

	//Increment request number
	reqNumber++;

	return retVal;
}

ResultStruct_t* reqFineGrainSim_batch(InputStruct_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;

	ResultStruct_t * retVal = (ResultStruct_t *)malloc(sizeof(ResultStruct_t) * numInputs);

	//Send requests
	int blockStart = reqNumber;
	for(int i = 0; i < numInputs; i++)
	{
		writeRequest(input[i], mpiRank, tag, dbHandle, reqNumber);
		reqNumber++;
	}

	//Get results
	///TODO

	return retVal;
}
