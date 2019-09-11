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

static int readCallback_icf(void *NotUsed, int argc, char **argv, char **azColName)
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

void writeRequest_icf(icf_request_t input, int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum, unsigned int reqType)
{
	//COMMENT: Is 2048 still enough?
	///TODO: Template on input type? Or just make one per input type?
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO REQS VALUES(\'%s\', %d, %d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d)", tag, mpiRank, reqNum, input.temperature, input.density[0], input.density[1], input.density[2], input.density[3], input.charges[0], input.charges[1], input.charges[2], input.charges[3], reqType);
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
	while( sqlRet != SQLITE_OK )
	{
		sqlRet = sqlite3_exec(dbHandle, sqlBuf, dummyCallback, 0, &zErrMsg);
		if(!(sqlRet == SQLITE_OK || sqlRet == SQLITE_BUSY || sqlRet == SQLITE_LOCKED))
		{
			fprintf(stderr, "Error in writeRequest_icf\n");
			fprintf(stderr, "SQL error: %s\n", zErrMsg);
			sqlite3_free(zErrMsg);
			sqlite3_close(dbHandle);
			exit(1);
		}
	}
	//Push the request number into the queue (set) for later use
	nastyGlobalSelectTable.tableMutex.lock();
	nastyGlobalSelectTable.reqQueue.insert(reqNum);
	nastyGlobalSelectTable.tableMutex.unlock();
	return;
}

int getReqNumber()
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;
	int retNum = reqNumber;
	reqNumber++;
	return retNum;
}

icf_result_t icf_req_single_with_reqtype(icf_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	int reqNumber = getReqNumber();

	icf_result_t retVal;

	char sqlBuf[2048];
	char *err = nullptr;

	///SQLite
	///  It provides a file-based DB. It has C, Python, and Klepto interfaces. As of sqlite3 it is probably somewhat
	///    performant with many concurrent writes and queries. And it will provide an easily queried DB for
	///    further study of the results to learn how to make our learners better
	///  Evidently the rest of the world has been right for 30-ish(?) years!
	///TABLE: (tag TEXT, rank INT, req INT, <inputs> REAL)

	//Send request
	writeRequest_icf(input, mpiRank, tag, dbHandle, reqNumber, reqType);

	//Spin on file until result is available
	bool haveResult = false;
	if(reqType == ALInterfaceMode_e::KILL)
	{
		haveResult = true;
	}
	while(!haveResult)
	{
		//Send SELECT with sqlite3_exec. 
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNumber, tag, mpiRank);
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_icf, 0, &err);
		while (rc != SQLITE_OK)
		{
			//THIS IS REALLY REALLY BAD: We can easily lock up if an expression is malformed
			rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_icf, 0, &err);
			if(!(rc == SQLITE_OK || rc == SQLITE_BUSY || rc == SQLITE_LOCKED))
			{
				fprintf(stderr, "Error in icf_req_single\n");
				fprintf(stderr, "SQL error: %s\n", err);

				sqlite3_free(err);
				sqlite3_close(dbHandle);
				exit(1);
			}
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

	return retVal;
}

icf_result_t icf_req_single(icf_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return icf_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

icf_result_t* icf_req_batch_with_reqtype(icf_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	int startReq = -1;

	icf_result_t * retVal = (icf_result_t *)malloc(sizeof(icf_result_t) * numInputs);

	char sqlBuf[2048];
	char *err = nullptr;

	//Send requests
	for(int i = 0; i < numInputs; i++)
	{
		int curReq = getReqNumber();
		if(startReq == -1)
		{
			startReq = curReq;
		}
		writeRequest_icf(input[i], mpiRank, tag, dbHandle, curReq, reqType);
	}

	//Get results (if you want them)
	bool haveResults = false;
	if(reqType == ALInterfaceMode_e::KILL)
	{
		haveResults = true;
	}
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
		int rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_icf, 0, &err);
		while (rc != SQLITE_OK)
		{
			rc = sqlite3_exec(dbHandle, sqlBuf, readCallback_icf, 0, &err);
			if(!(rc == SQLITE_OK || rc == SQLITE_BUSY || rc == SQLITE_LOCKED))
			{
				fprintf(stderr, "Error in icf_req_single\n");
				fprintf(stderr, "SQL error: %s\n", err);
				
				sqlite3_free(err);
				sqlite3_close(dbHandle);
				exit(1);
			}
		}
		//SQL did something, so Get lock
		nastyGlobalSelectTable.tableMutex.lock();
		//Are all requests processed?
		haveResults = nastyGlobalSelectTable.reqQueue.empty();
		nastyGlobalSelectTable.tableMutex.unlock();
	}

	//All requests have been procssed, so pull them
	nastyGlobalSelectTable.tableMutex.lock();
	int curReq = startReq;
	for(int i = 0; i < numInputs; i++)
	{
		///TODO: Add in an error check
		retVal[i] = nastyGlobalSelectTable.resultTable.find(curReq)->second;
		curReq++;
	}
	nastyGlobalSelectTable.tableMutex.unlock();


	return retVal;
}

icf_result_t* icf_req_batch(icf_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return icf_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void icf_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle)
{
	icf_request_t req;
	req.temperature = -0.0;
	for(int i = 0; i < 4; i++)
	{
		req.density[i] = -0.0;
		req.charges[i] = -0.0;
	}

	icf_req_single_with_reqtype(req, mpiRank, tag, dbHandle, ALInterfaceMode_e::KILL);
	return;
}

lbmZeroD_result_t lbmZeroD_req_single(lbmZeroD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return lbmZeroD_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

lbmZeroD_result_t lbmZeroD_req_single_with_reqtype(lbmZeroD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	lbmZeroD_result_t retVal;
	///TODO
	exit(1);
	return retVal;
}

void lbmZeroD_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle)
{
	lbmZeroD_request_t req;
	req.distance = -0.0;
	req.density = -0.0;
	req.temperature = -0.0;

	lbmZeroD_req_single_with_reqtype(req, mpiRank, tag, dbHandle, ALInterfaceMode_e::KILL);
	return;
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