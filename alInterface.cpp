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
	//Check if request has been processed yet
	auto reqIter = nastyGlobalSelectTable.reqQueue.find(reqID);
	if (reqIter != nastyGlobalSelectTable.reqQueue.end())
	{
		//Write result to global map so we can use it
		nastyGlobalSelectTable.resultTable[reqID] = result;
		nastyGlobalSelectTable.tableMutex.unlock();
		//And remove request from queue in case we get duplicate results
		nastyGlobalSelectTable.reqQueue.erase(reqIter);
	}

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
		//THIS IS REALLY REALLY BAD: We can easily lock up if an expression is malformed
		sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
		// fprintf(stderr, "Error in writeRequest\n");
		// fprintf(stderr, "SQL error: %s\n", zErrMsg);
		// sqlite3_free(zErrMsg);
		// exit(1);
	}
	//Push the request number into the queue (set) for later use
	nastyGlobalSelectTable.tableMutex.lock();
	nastyGlobalSelectTable.reqQueue.insert(reqNum);
	nastyGlobalSelectTable.tableMutex.unlock();
	return;
}

ResultStruct_t reqFineGrainSim_single(InputStruct_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;

	ResultStruct_t retVal;

	char sqlBuf[2048];
	char *err = nullptr;

	///SQLite
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
		//Send SELECT with sqlite3_exec. 
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNumber, tag, mpiRank);
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
		while (rc != SQLITE_OK)
		{
			//THIS IS REALLY REALLY BAD: We can easily lock up if an expression is malformed
			rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
			// fprintf(stderr, "Error in reqFineGrainSim_single\n");
			// fprintf(stderr, "SQL error: %s\n", err);

			// sqlite3_free(err);
			// sqlite3_close(dbHandle);
			// exit(1);
		}
		//SQL did something, so Get lock
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

	char sqlBuf[2048];
	char *err = nullptr;

	//Send requests
	int curReq = reqNumber;
	for(int i = 0; i < numInputs; i++)
	{
		writeRequest(input[i], mpiRank, tag, dbHandle, curReq);
		curReq++;
	}

	//Get results
	bool haveResults = false;
	while(!haveResults)
	{
		//Get bounds of unfulfilled requests: Lock to attempt thread safety
		nastyGlobalSelectTable.tableMutex.lock();
		int start = * nastyGlobalSelectTable.reqQueue.begin();
		auto nextToLast = nastyGlobalSelectTable.reqQueue.end();
		nextToLast--;
		int end = * nextToLast;
		nastyGlobalSelectTable.tableMutex.unlock();

		//Send SELECT with sqlite3_exec. 
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ>=%d AND REQ<=%d AND TAG=\'%s\' AND RANK=%d;", start, end, tag, mpiRank);
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
		while (rc != SQLITE_OK)
		{
			//THIS IS REALLY REALLY BAD: We can easily lock up if an expression is malformed
			rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_single, 0, &err);
			// fprintf(stderr, "Error in reqFineGrainSim_single\n");
			// fprintf(stderr, "SQL error: %s\n", err);

			// sqlite3_free(err);
			// sqlite3_close(dbHandle);
			// exit(1);
		}
		//SQL did something, so Get lock
		nastyGlobalSelectTable.tableMutex.lock();
		//Are all requests processed?
		haveResults = nastyGlobalSelectTable.reqQueue.empty();
		nastyGlobalSelectTable.tableMutex.unlock();
	}

	//All requests have been procssed, so pull them
	nastyGlobalSelectTable.tableMutex.lock();
	curReq = reqNumber;
	for(int i = 0; i < numInputs; i++)
	{
		///TODO: Add in an error check
		retVal[i] = nastyGlobalSelectTable.resultTable.find(curReq)->second;
		curReq++;
	}
	nastyGlobalSelectTable.tableMutex.unlock();

	//Increment reqNumber
	reqNumber += numInputs;

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