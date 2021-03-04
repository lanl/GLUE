#include "alInterface.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <tuple>
#include <iterator>
#include <algorithm>
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
sqlite3* globalGlueDBHandle;
const unsigned int globalGlueBufferSize = 1024;

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

bgk_result_t bgk_req_single_with_reqtype(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<bgk_request_t, bgk_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

bgk_result_t bgk_req_single(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return bgk_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

bgk_result_t* bgk_req_batch_with_reqtype(bgk_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<bgk_request_t, bgk_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
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

bgkmasses_result_t bgkmasses_req_single_with_reqtype(bgkmasses_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<bgkmasses_request_t, bgkmasses_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

bgkmasses_result_t bgkmasses_req_single(bgkmasses_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return bgkmasses_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

bgkmasses_result_t* bgkmasses_req_batch_with_reqtype(bgkmasses_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<bgkmasses_request_t, bgkmasses_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
}

bgkmasses_result_t* bgkmasses_req_batch(bgkmasses_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return bgkmasses_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void bgkmasses_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle)
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

lbmToOneDMD_result_t lbmToOneDMD_req_single(lbmToOneDMD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return lbmToOneDMD_req_single_with_reqtype(input, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

lbmToOneDMD_result_t lbmToOneDMD_req_single_with_reqtype(lbmToOneDMD_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_single_with_reqtype<lbmToOneDMD_request_t, lbmToOneDMD_result_t>(input, mpiRank, tag, dbHandle, reqType);
}

lbmToOneDMD_result_t* lbmToOneDMD_req_batch_with_reqtype(lbmToOneDMD_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType)
{
	return req_batch_with_reqtype<lbmToOneDMD_request_t, lbmToOneDMD_result_t>(input, numInputs, mpiRank, tag, dbHandle, reqType);
}

lbmToOneDMD_result_t* lbmToOneDMD_req_batch(lbmToOneDMD_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle)
{
	return lbmToOneDMD_req_batch_with_reqtype(input, numInputs, mpiRank, tag, dbHandle, ALInterfaceMode_e::DEFAULT);
}

void lbmToOneDMD_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle)
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
	sqlite3 *dbHandle;
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
	int myRank;
	MPI_Comm_rank(glueComm, &myRank);
	if(myRank == 0)
	{
		//Connect to that DB
		sqlite3_open(fName, &globalGlueDBHandle);
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

std::tuple<int,int> icf_insertReqs(bgk_request_t *input, int numInputs, int reqRank, sqlite3 * dbHandle)
{
	std::string tag("TAG");
	int start,end;
	for(int i = 0; i < numInputs; i++)
	{
		int reqNum = getReqNumberForRank(reqRank);
		if(i == 0)
		{
			start = reqNum;
		}
		else if(i == numInputs - 1)
		{
			end = reqNum;
		}
		///TODO: Remove "TAG" requirement
		writeRequest<bgk_request_t>(input[i], reqRank, const_cast<char *>(tag.c_str()), dbHandle, reqNum, ALInterfaceMode_e::DEFAULT);
	}
	std::tuple<int, int> reqRange(start, end);
	return reqRange;
}

std::vector<bgk_result_t> * icf_extractResults(std::tuple<int, int> reqRange, int reqRank, sqlite3 *dbHandle)
{
	///TODO: Consider thought to reducing memory footprint because we can potentially use 2N for this
	std::vector<bgk_result_t> * retVec = new std::vector<bgk_result_t>(std::get<1>(reqRange) - std::get<0>(reqRange) + 1);
	// Similar logic to in alInterface.py:pollAndProcessFGSRequests
	//  Get Results from std::get<0>reqRange  until std::get<1>reqRange
	//  Highest result id is new nextExpected
	//  Use missingSet to ensure that all IDs from std::get<0>reqRange to nextExpected are received and, if not, insert
	//  Repeat request for results from *missingSet.begin() to std::get<1>reqRange until
	//    missingSet.empty() && nextExpected > std::get<1>reqRange
	return retVec;
}

bgk_result_t* icf_req(bgk_request_t *input, int numInputs, MPI_Comm glueComm)
{
	//Thanks to Andrew Reisner for helping with a lot of the thought process behind the MPI aspects of the algorithm
	///TODO: Will probably refactor to a template
	//Get clueComm rank and size
	int myRank, commSize;
	MPI_Comm_rank(glueComm, &myRank);
	MPI_Comm_size(glueComm, &commSize);
	//Compute number of required request batches
	std::vector<int> reqBatches(commSize, 0);
	reqBatches[myRank] = numInputs / globalGlueBufferSize;
	if(numInputs % globalGlueBufferSize != 0)
	{
		reqBatches[myRank]++;
	}
	//Reduce to provide that to 0
	MPI_Reduce(reqBatches.data(), reqBatches.data(), commSize, MPI_INT, MPI_MAX, 0, glueComm);
	//Prepare results buffer
	bgk_result_t* resultsBuffer = (bgk_result_t*)malloc(sizeof(bgk_result_t*) * numInputs);
	//If rank 0
	if(myRank == 0)
	{
		std::vector<std::vector<std::tuple<int,int>>> reqsPerBatch;
		//First, submit all rank 0 requests
		std::tuple<int, int> zeroReqs = icf_insertReqs(input, numInputs, 0, globalGlueDBHandle);
		reqsPerBatch[0].push_back(zeroReqs);
		//Then, do the rest
		std::vector<int> resultBatches(reqBatches);
		std::vector<bgk_request_t> reqs(globalGlueBufferSize);
		for(int rank = 1; rank < commSize; rank++)
		{
			//Do we still have requests from that rank?
			if(reqBatches[rank] != 0)
			{
				//Blocking recv those requests
				MPI_Status reqStatus;
				MPI_Recv(reqs.data(), globalGlueBufferSize*sizeof(bgk_request_t), MPI_BYTE, rank, reqBatches[rank], glueComm, &reqStatus);
				//And determine how many were actually sent to us
				int numReqs;
				MPI_Get_count(&reqStatus, MPI_BYTE, &numReqs);
				numReqs = numReqs / sizeof(bgk_request_t);
				//Send to glue code
				std::tuple<int, int> batchRange  = icf_insertReqs(reqs.data(), numReqs, rank, globalGlueDBHandle);
				// Put requests in req list
				reqsPerBatch[rank].push_back(batchRange);
				//And decrement the number of expected batches from this rank
				reqBatches[rank]--;
			}
		}
		//Now, we process results
		for(int rank = 1; rank < commSize; rank++)
		{
			//Do we still have results for that rank?
			if(resultBatches[rank] != 0)
			{
				//Get results
				std::vector<bgk_result_t> * batchResults = icf_extractResults(reqsPerBatch[rank][resultBatches[rank]], rank, globalGlueDBHandle);
				//Send results with a BLOCKING send
				///TODO send batchResults.data()
				//Free memory
				delete batchResults;
				//And decrement result batches counter
				resultBatches[rank]--;
			}
		}
		//And then handle the requests from rank 0
		std::vector<bgk_result_t> * batchResults = icf_extractResults(reqsPerBatch[0][1], 0, globalGlueDBHandle);
		memcpy(resultsBuffer, batchResults->data(), numInputs*sizeof(bgk_result_t));
		delete batchResults;
	}
	else
	{
		//Everyone else, send your requests to rank 0
		unsigned int curIndex = 0;
		std::vector<MPI_Request> sendReqs(reqBatches[myRank]);
		std::vector<MPI_Status> sendStatuses(reqBatches[myRank]);
		for(int i = reqBatches[myRank]; i > 0; i--)
		{
			//Compute size of send
			int reqSize;
			if(curIndex + globalGlueBufferSize > numInputs)
			{
				reqSize = numInputs - curIndex;
			}
			else
			{
					reqSize = globalGlueBufferSize;
			}
			//Queue up send of this data to rank 0
			MPI_Isend(&input[curIndex], sizeof(bgk_request_t)*reqSize, MPI_BYTE, 0, i, glueComm, &sendReqs[i-1]);
			//Increment curIndex
			curIndex += globalGlueBufferSize;
		}
		//Wait on all the sends
		MPI_Waitall(reqBatches[myRank], sendReqs.data(), sendStatuses.data());
		//Then get results
		for(int i = 0; i < reqBatches[myRank]; i++)
		{
			//Blocking recv for results
			///TODO
		}
	}
	//Return results
	return resultsBuffer;
}

void closeGlue(MPI_Comm glueComm)
{
	//Not a collective operation because only rank 0 needs to do this
	//If glueComm rank is 0
	int myRank;
	MPI_Comm_rank(glueComm, &myRank);
	if(myRank == 0)
	{
		///TODO: Send killswitch
		//Disconnect from that DB
		sqlite3_close(globalGlueDBHandle);
	}
}
