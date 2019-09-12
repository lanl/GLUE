#include "alInterface.hpp"

#include <cstdio>
#include <cstdlib>
#include <sqlite3.h>
#include <unordered_set>

///TODO: Verify this is the correct way to do a global variable
AsyncSelectTable_t<bgk_result_t> globalBGKResultTable;
AsyncSelectTable_t<lbmZeroD_result_t> globalLBMZeroDResultTable;

static int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName)
{
	//Do nothing. We don't need a result from this op
	return 0;
}

static int readCallback_bgk(void *NotUsed, int argc, char **argv, char **azColName)
{
	//Process row: Ignore 0 (tag) and 1 (rank)
	int reqID = atoi(argv[2]);
	bgk_result_t result;

	//Add results
	result.viscosity = atof(argv[3]);
	result.thermalConductivity = atof(argv[4]);
	for(int i = 0; i < 10; i++)
	{
		result.diffusionCoefficient[i] = atof(argv[i+5]);
	}

	//Get global select table of type bgk_result_t
	globalBGKResultTable.tableMutex.lock();
	//Check if request has been processed yet
	auto reqIter = globalBGKResultTable.resultTable.find(reqID);
	if (reqIter == globalBGKResultTable.resultTable.end())
	{
		//Write result to global map so we can use it
		globalBGKResultTable.resultTable[reqID] = result;
	}
	globalBGKResultTable.tableMutex.unlock();

	return 0;
}

int getReqNumber()
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;
	int retNum = reqNumber;
	reqNumber++;
	return retNum;
}

bgk_result_t bgk_req_single_with_reqtype(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	int reqNumber = getReqNumber();

	bgk_result_t retVal;

	//Send request
	writeRequest<bgk_request_t>(input, mpiRank, tag, dbHandle, reqNumber, reqType);

	//Read result
	retVal = readResult_blocking<bgk_result_t>(mpiRank, tag, dbHandle, reqNumber, reqType);

	return retVal;
}

bgk_result_t bgk_req_single(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return bgk_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

bgk_result_t* bgk_req_batch_with_reqtype(bgk_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	std::unordered_set<int> reqQueue;
	bgk_result_t * retVal = (bgk_result_t *)malloc(sizeof(bgk_result_t) * numInputs);
	//Start all requests
	for(int i = 0; i < numInputs; i++)
	{
		int reqNumber = getReqNumber();
		writeRequest<bgk_request_t>(input[i], mpiRank, tag, dbHandle, reqNumber, reqType);
		reqQueue.insert(reqNumber);
	}

	//Process requests
	//In this case we block on each request so it is pretty simple
	int retValCounter = 0;
	for(auto curReq = reqQueue.begin(); curReq != reqQueue.end(); curReq++)
	{
		retVal[retValCounter] = readResult_blocking<bgk_result_t>(mpiRank, tag, dbHandle, *curReq, reqType);
		retValCounter++;
	}

	return retVal;
}

bgk_result_t* bgk_req_batch(bgk_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return bgk_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void bgk_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle)
{
	bgk_request_t req;
	req.temperature = -0.0;
	for(int i = 0; i < 4; i++)
	{
		req.density[i] = -0.0;
		req.charges[i] = -0.0;
	}

	bgk_req_single_with_reqtype(req, mpiRank, tag, dbHandle, ALInterfaceMode_e::KILL);
	return;
}

lbmZeroD_result_t lbmZeroD_req_single(lbmZeroD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return lbmZeroD_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

lbmZeroD_result_t lbmZeroD_req_single_with_reqtype(lbmZeroD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	int reqNumber = getReqNumber();

	lbmZeroD_result_t retVal;

	//Send request
	writeRequest<lbmZeroD_request_t>(input, mpiRank, tag, dbHandle, reqNumber, reqType);

	//Read result
	retVal = readResult_blocking<lbmZeroD_result_t>(mpiRank, tag, dbHandle, reqNumber, reqType);

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