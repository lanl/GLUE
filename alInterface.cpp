#include "alInterface.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <tuple>
#include <iterator>
#include <algorithm>
#include <numeric>
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

std::unique_ptr<std::vector<int>> icf_insertReqs(bgk_request_t *input, int numInputs, int reqRank, sqlite3 * dbHandle)
{
	//Return  a full vector as we have no guarantee of contiguous reqIDs
	auto retVec = std::make_unique<std::vector<int>>(numInputs, -1);
	std::string tag("TAG");
	int start,end;
	int reqNum;
	for(int i = 0; i < numInputs; i++)
	{
		reqNum = getReqNumberForRank(reqRank);
		(*retVec)[i] = reqNum;
		///TODO: Remove "TAG" requirement
		writeRequest<bgk_request_t>(input[i], reqRank, const_cast<char *>(tag.c_str()), dbHandle, reqNum, ALInterfaceMode_e::DEFAULT);
	}
	return retVec;
}


std::vector<bgk_result_t> * icf_extractResults(std::unique_ptr<std::vector<int>> &reqRange, int reqRank, sqlite3 *dbHandle)
{
	///TODO: Consider thought to reducing memory footprint because we can potentially use 2N for this
	std::vector<bgk_result_t> * retVec = new std::vector<bgk_result_t>(reqRange->size());
	
	//We have guarantee that reqRange[0] is lowest ID but not that all IDs are contiguous
	//Need to request lowest to max until all results have been received
	//

	// Start by requesting the full range
	

/*

	// Similar logic to in alInterface.py:pollAndProcessFGSRequests
	std::set<int> missingSet;
	
	int nextExpected = std::get<0>(reqRange);
	int maxExpected = std::get<1>(reqRange);
	int latestID = nextExpected;
	while(nextExpected <= maxExpected || missingSet.empty() != true)
	{
		//  Get Results from nextExpected  until maxExpected
		std::vector<std::tuple<int,bgk_result_t>> sqlResults = getRangeOfResults<bgk_result_t>(nextExpected, maxExpected, reqRank, dbHandle, ALInterfaceMode_e::DEFAULT);
		// Pull maxID from that
		auto maxIter = std::max_element(sqlResults.begin(), sqlResults.end(), reqIDMin<bgk_result_t>);
		//Is the maxID greater than our previous latestID?
		if(std::get<0>(*maxIter) > latestID)
		{
			//It is, add the difference to the missingSet so we can tick those off
			int newLatest =  std::get<0>(*maxIter);
			int latestDelta = newLatest - latestID + 1;
			///TODO: Probably a better way to do this
			//Basically a python range() statement
			std::vector<int> newMissing(latestDelta);
			std::iota(newMissing.begin(), newMissing.end(), latestID);
			///Super expensive insert into the set
			missingSet.insert(newMissing.begin(), newMissing.end());
			//And then update latestID
			latestID = newLatest;
		}
		// Process Results (basically copy to retVec) and find MaxID
		for (auto it = sqlResults.begin(); it != sqlResults.end(); ++it)
		{
			//Get the request ID
			int reqID = std::get<0>(*it);
			//Is this an ID that was in our missingSet? (it should be?)
			if(missingSet.empty() != true)
			{
				auto missingIt = missingSet.find(reqID);
				if(missingIt != missingSet.end())
				{
					//It was found so we need to remove it
					missingSet.erase(missingIt);
				}
				//And copy in data
				(*retVec)[reqID] = std::get<1>(*it);
			}
		}
		// Are we still missing any entries?
		if(missingSet.empty())
		{
			//If not then the next expected is latestID+1
			nextExpected = latestID+1;
		}
		else
		{
			//We are so it will be the lowest reqID that we are missing
			nextExpected = *(missingSet.begin());
		}
	}
*/
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
	std::vector<int> localReqBatches(commSize, 0);
	std::vector<int> reqBatches(commSize, 0);
	localReqBatches[myRank] = numInputs / globalGlueBufferSize;
	if(numInputs % globalGlueBufferSize != 0)
	{
		localReqBatches[myRank]++;
	}
	//Reduce to provide that to 0
	MPI_Reduce(localReqBatches.data(), reqBatches.data(), commSize, MPI_INT, MPI_MAX, 0, glueComm);
	//Prepare results buffer
	bgk_result_t* resultsBuffer = static_cast<bgk_result_t*>(malloc(sizeof(bgk_result_t) * numInputs));
	//If rank 0
	if(myRank == 0)
	{
		std::vector<int> resultBatches(reqBatches);
		//A vector of vectors of unique pointers to vectors of request ID mappings
		std::vector<std::vector<std::unique_ptr<std::vector<int>>>> reqsPerBatch(commSize);
		//First, submit all rank 0 requests
		auto zeroReqs = icf_insertReqs(input, numInputs, 0, globalGlueDBHandle);
		reqsPerBatch[0].push_back(std::move(zeroReqs));
		//And we know we have one batch for zero because it is special
		resultBatches[0] = 1;
		//Then, do the rest
		std::vector<bgk_request_t> reqs(globalGlueBufferSize);
		for(int rank = 1; rank < commSize; rank++)
		{
			//Do we still have requests from that rank?
			if(reqBatches[rank] != 0)
			{
				//Blocking recv those requests
				MPI_Status reqStatus;
				//MPI IDs decrement [total, 1]
				MPI_Recv(reqs.data(), globalGlueBufferSize*sizeof(bgk_request_t), MPI_BYTE, rank, reqBatches[rank], glueComm, &reqStatus);
				//And determine how many were actually sent to us
				int numReqs;
				MPI_Get_count(&reqStatus, MPI_BYTE, &numReqs);
				numReqs = numReqs / sizeof(bgk_request_t);
				//Send to glue code
				auto batchRange  = icf_insertReqs(reqs.data(), numReqs, rank, globalGlueDBHandle);
				// Put requests in req list
				reqsPerBatch[rank].push_back(std::move(batchRange));
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
				//Get results from glue code
				std::vector<bgk_result_t> * batchResults = icf_extractResults(reqsPerBatch[rank][resultBatches[rank]], rank, globalGlueDBHandle);
				//Send results with a BLOCKING send
				// Need to do blocking sends because of memory concerns
				//MPI IDs decrement [total, 1]
				MPI_Send(batchResults->data(), batchResults->size()*sizeof(bgk_result_t), MPI_BYTE, rank, resultBatches[rank], glueComm); 
				//Free memory
				delete batchResults;
				//And decrement result batches counter
				resultBatches[rank]--;
			}
		}
		//And then handle the requests from rank 0
		std::vector<bgk_result_t> * batchResults = icf_extractResults(reqsPerBatch[0][0], 0, globalGlueDBHandle);
		std::copy(batchResults->begin(), batchResults->end(), resultsBuffer);
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
			// non-blocking send as we aren't going to clobber the send buffers
			//MPI IDs decrement [total, 1]
			MPI_Isend(&input[curIndex], sizeof(bgk_request_t)*reqSize, MPI_BYTE, 0, i, glueComm, &sendReqs[i-1]);
			//Increment curIndex
			curIndex += globalGlueBufferSize;
		}
		//Wait on all the sends
		MPI_Waitall(reqBatches[myRank], sendReqs.data(), sendStatuses.data());
		//Then get results
		curIndex = 0;
		std::vector<MPI_Request> recvReqs(reqBatches[myRank]);
		std::vector<MPI_Status> recvStatuses(reqBatches[myRank]);
		for(int i = reqBatches[myRank]; i > 0; i--)
		{
			//Compute size of recv
			int reqSize;
			if(curIndex + globalGlueBufferSize > numInputs)
			{
				reqSize = numInputs - curIndex;
			}
			else
			{
				reqSize = globalGlueBufferSize;
			}
			//Recv for results
			// non-blocking because we are writing straight to results buffer
			//MPI IDs decrement [total, 1]
			MPI_Irecv(&resultsBuffer[curIndex], sizeof(bgk_result_t)*reqSize, MPI_BYTE, 0, i, glueComm, &recvReqs[i-1]);
			//Increment curIndex
			curIndex += globalGlueBufferSize;
		}
		MPI_Waitall(reqBatches[myRank], recvReqs.data(), recvStatuses.data());
	}
	//Return results
	return resultsBuffer;
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
