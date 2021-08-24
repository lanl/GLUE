#include "alInterface.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <tuple>
#include <iterator>
#include <memory>
#include <sqlite3.h>
#include <mpi.h>

#ifdef DB_EXISTENCE_SPIN
#include <experimental/filesystem>
#include <thread>
#include <chrono>
#endif

///TODO: Verify this is the correct way to do a global variable
AsyncSelectTable_t<bgk_result_t> globalBGKResultTable;
AsyncSelectTable_t<lbmToOneDMD_result_t> globallbmToOneDMDResultTable;
std::vector<AsyncSelectTable_t<bgk_result_t>> globalColBGKResultTable;
sqlite3* globalGlueDBHandle;
const unsigned int globalGlueBufferSize = 1024;

int getReqNumber()
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;
	int retNum = reqNumber;
	reqNumber++;
	return retNum;
}

int getReqNumberForRank(int rank)
{
	//Static variables are dirty but this is an okay use
	static std::vector<int> reqNumber;
	if (reqNumber.size() <= rank)
	{
		reqNumber.resize(rank+1, 0);
	}
	int retVal = reqNumber[rank];
	reqNumber[rank]++;
	return retVal;
}

bgk_result_t bgk_req_single_with_reqtype(bgk_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<bgk_request_t, bgk_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

bgk_result_t bgk_req_single(bgk_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return bgk_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

bgk_result_t* bgk_req_batch_with_reqtype(bgk_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<bgk_request_t, bgk_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
}

bgk_result_t* bgk_req_batch(bgk_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return bgk_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void bgk_stop_service(int mpiRank, char * tag, dbHandle_t dbHandle)
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

bgkmasses_result_t bgkmasses_req_single_with_reqtype(bgkmasses_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<bgkmasses_request_t, bgkmasses_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

bgkmasses_result_t bgkmasses_req_single(bgkmasses_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return bgkmasses_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

bgkmasses_result_t* bgkmasses_req_batch_with_reqtype(bgkmasses_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<bgkmasses_request_t, bgkmasses_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
}

bgkmasses_result_t* bgkmasses_req_batch(bgkmasses_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return bgkmasses_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void bgkmasses_stop_service(int mpiRank, char * tag, dbHandle_t dbHandle)
{
	bgkmasses_request_t req;
	req.temperature = -0.0;
	for(int i = 0; i < 4; i++)
	{
		req.density[i] = -0.0;
		req.charges[i] = -0.0;
		req.masses[i] = -0.0;
	}

	bgkmasses_req_single_with_reqtype(req, mpiRank, tag, dbHandle, ALInterfaceMode_e::KILL);
	return;
}

lbmToOneDMD_result_t lbmToOneDMD_req_single(lbmToOneDMD_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return lbmToOneDMD_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

lbmToOneDMD_result_t lbmToOneDMD_req_single_with_reqtype(lbmToOneDMD_request_t input, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<lbmToOneDMD_request_t, lbmToOneDMD_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

lbmToOneDMD_result_t* lbmToOneDMD_req_batch_with_reqtype(lbmToOneDMD_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<lbmToOneDMD_request_t, lbmToOneDMD_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
}

lbmToOneDMD_result_t* lbmToOneDMD_req_batch(lbmToOneDMD_request_t *input, int numInputs, int mpiRank, char * tag, dbHandle_t dbHandle)
{
	return lbmToOneDMD_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void lbmToOneDMD_stop_service(int mpiRank, char * tag, dbHandle_t dbHandle)
{
	lbmToOneDMD_request_t req;
	req.distance = -0.0;
	req.density = -0.0;
	req.temperature = -0.0;

	lbmToOneDMD_req_single_with_reqtype(req, mpiRank, tag, dbHandle, ALInterfaceMode_e::KILL);
	return;
}

sqlite3* initDB(int mpiRank, char * fName)
{
#ifdef DB_EXISTENCE_SPIN
	while(!std::experimental::filesystem::exists(fName))
	{
		std::this_thread::sleep_for (std::chrono::seconds(1));
	}
#endif
	dbHandle_t dbHandle;
	sqlite3_open(fName, &dbHandle);
	return dbHandle;
}

void closeDB(sqlite3* dbHandle)
{
	sqlite3_close(dbHandle);
}

void resFreeWrapper(void * buffer)
{
	free(buffer);
}

void connectGlue(char * fName, MPI_Comm glueComm)
{
	//Not a collective operation because only rank 0 needs to do this
	//If glueComm rank is 0
	int myRank, commSize;
	MPI_Comm_rank(glueComm, &myRank);
	MPI_Comm_size(glueComm, &commSize);
	if(myRank == 0)
	{
		//Connect to that DB
		sqlite3_open(fName, &globalGlueDBHandle);
		//And resize result table
		globalColBGKResultTable.resize(commSize);
	}
}

void preprocess_icf(bgk_request_t *input, int numInputs, bgk_request_t **processedInput, int * numProcessedInputs)
{
	//Look for and remove duplicates
	///TODO
	*processedInput = input;
	*numProcessedInputs = numInputs;
	return;
}

bgk_result_t* icf_req(bgk_request_t *input, int numInputs, MPI_Comm glueComm)
{
	return req_collective<bgk_request_t, bgk_result_t>(input, numInputs, glueComm);
}

void closeGlue(MPI_Comm glueComm)
{
	///TODO: Template this to send appropriate packet type
	//Not a collective operation because only rank 0 needs to do this
	//If glueComm rank is 0
	int myRank;
	MPI_Comm_rank(glueComm, &myRank);
	if(myRank == 0)
	{
		std::string tag("TAG");
		//Engage that killswitch
		bgk_stop_service(0, const_cast<char *>(tag.c_str()), globalGlueDBHandle);
		//Disconnect from that DB
		sqlite3_close(globalGlueDBHandle);
	}
}

int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName)
{
	//Do nothing. We don't need a result from this op
	return 0;
}

int readCallback_bgk(void *NotUsed, int argc, char **argv, char **azColName)
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
	result.provenance = atoi(argv[15]);

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

int readCallback_colbgk(void *NotUsed, int argc, char **argv, char **azColName)
{
	//Process row: Ignore 0 (tag)
	int rank = atoi(argv[1]);
	int reqID = atoi(argv[2]);
	bgk_result_t result;

	//Add results
	result.viscosity = atof(argv[3]);
	result.thermalConductivity = atof(argv[4]);
	for(int i = 0; i < 10; i++)
	{
		result.diffusionCoefficient[i] = atof(argv[i+5]);
	}
	result.provenance = atoi(argv[15]);

	//Get global select table of type bgk_result_t
	globalColBGKResultTable[rank].tableMutex.lock();
	//Check if request has been processed yet
	auto reqIter = globalColBGKResultTable[rank].resultTable.find(reqID);
	if (reqIter == globalColBGKResultTable[rank].resultTable.end())
	{
		//Write result to global map so we can use it
		globalColBGKResultTable[rank].resultTable[reqID] = result;
	}
	globalColBGKResultTable[rank].tableMutex.unlock();

	return 0;
}


