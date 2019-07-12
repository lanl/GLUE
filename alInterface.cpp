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
	result.viscosity = atof(argv[3]);
	result.thermalConductivity = atof(argv[4]);
	for(int i = 0; i < 10; i++)
	{
		result.diffusionCoefficient[i] = atof(argv[i+5]);
	}

	nastyGlobalSelectTable.tableMutex.lock();
	nastyGlobalSelectTable.resultTable[reqID] = result;
	nastyGlobalSelectTable.tableMutex.unlock();	

	return 0;
}

void writeRequest(InputStruct_t input, int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum)
{
	//COMMENT: Is 2048 still enough?
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO REQS VALUES(\'%s\', %d, %d, %f, %f, %f, %f, %f, %f, %f, %f, %f)", tag, mpiRank, reqNum, input.temperature, input.density[0], input.density[1], input.density[2], input.density[3], input.charges[0], input.charges[1], input.charges[2], input.charges[3]);
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
	while( sqlRet != SQLITE_OK )
	{
		//THIS IS REALLY REALLY BAD
		sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
		// fprintf(stderr, "Error in writeRequest\n");
		// fprintf(stderr, "SQL error: %s\n", zErrMsg);
		// sqlite3_free(zErrMsg);
		// exit(1);
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
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNumber, tag, mpiRank);
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
		while (rc != SQLITE_OK)
		{
			//THIS IS REALLY REALLY BAD
			rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
			// fprintf(stderr, "Error in reqFineGrainSim_single\n");
			// fprintf(stderr, "SQL error: %s\n", err);

			// sqlite3_free(err);
			// sqlite3_close(dbHandle);
			// exit(1);
		}
		// fprintf(stdout, "Processing REQ=%d\n", reqNumber);
		// fflush(stdout);
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

sqlite3* initDB(int mpiRank, char * fName)
{
	sqlite3 *dbHandle;
	sqlite3_open(fName, &dbHandle);
	return dbHandle;
}

void closeDB(sqlite3* dbHandle)
{
	sqlite3_close(dbHandle);
}