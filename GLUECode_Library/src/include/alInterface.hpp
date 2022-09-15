#ifndef __alInterface_hpp
#define __alInterface_hpp

#include "alInterface.h"
#include "alDBInterfaces.hpp"
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <vector>
#include <tuple>
#include <queue>
#include <memory>
#include <algorithm>

/**
 * @brief Getter for monotonically increasing ID for GLUE requests for serial applications
 *
 * @return int ID to use for GLUE request
 */
int getReqNumber();
/**
 * @brief Getter for monotonically increasing ID for GLUE requests for distributed memory applications
 *
 * @param rank Unique identifier for requester. Based on concept of MPI Rank
 * @return int ID to use for GLUE request
 */
int getReqNumberForRank(int rank);

/**
 * @brief Struct/wrapper for thread-safe global map of request IDs to results to process `SELECT` statements
 *
 * @tparam T The type of result to store
 */
template <typename T> struct AsyncSelectTable_t
{
	std::map<int, T> resultTable;
	std::mutex tableMutex;

	AsyncSelectTable_t<T>()
	{

	}
	AsyncSelectTable_t<T>(const AsyncSelectTable_t<T> &p2)
	{
		resultTable = p2.resultTable;
		///TODO: This should probably use a smart pointer to share the mutex
	}
};

extern AsyncSelectTable_t<bgk_result_t> globalBGKResultTable;
extern std::vector<AsyncSelectTable_t<bgk_result_t>> globalColBGKResultTable;
extern AsyncSelectTable_t<lbmToOneDMD_result_t> globallbmToOneDMDResultTable;
extern dbHandle_t globalGlueDBHandle;
extern const unsigned int globalGlueBufferSize;

/**
 * @brief Get the Global Table object for specified type
 *
 * @tparam T The result type of the table to get
 * @return Reference to global table or exit if unsupported type
 */
template <typename T> AsyncSelectTable_t<T>& getGlobalTable()
{
	exit(1);
}
template <> AsyncSelectTable_t<bgk_result_t>& getGlobalTable<bgk_result_t>()
{
	return globalBGKResultTable;
}
template <> AsyncSelectTable_t<lbmToOneDMD_result_t>& getGlobalTable<lbmToOneDMD_result_t>()
{
	return globallbmToOneDMDResultTable;
}

template <typename T> AsyncSelectTable_t<T>& getGlobalColTable(int rank)
{
	exit(1);
}
template <> AsyncSelectTable_t<bgk_result_t>& getGlobalColTable<bgk_result_t>(int rank)
{
	return globalColBGKResultTable[rank];
}

/**
 * @brief Get insertion string for SQL insertion command
 *
 * @tparam T Type of the request to generate a string for
 * @param input Request to insert into table
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param reqNum ID of request
 * @param reqType ALInterfaceMode_e of request type
 * @return std::string SQL insertion command to submit or error if unsupported type
 */
template <typename T> std::string getReqSQLString(T input, int mpiRank, char * tag, int reqNum, unsigned int reqType)
{
	exit(1);
}
template <> std::string getReqSQLString<bgk_request_t>(bgk_request_t input, int mpiRank, char * tag, int reqNum, unsigned int reqType)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO BGKREQS VALUES(\'%s\', %d, %d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d)", tag, mpiRank, reqNum, input.temperature, input.density[0], input.density[1], input.density[2], input.density[3], input.charges[0], input.charges[1], input.charges[2], input.charges[3], reqType);
	std::string retString(sqlBuf);
	return retString;
}
template <> std::string getReqSQLString<bgkmasses_request_t>(bgkmasses_request_t input, int mpiRank, char * tag, int reqNum, unsigned int reqType)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "INSERT INTO BGKMASSESREQS VALUES(\'%s\', %d, %d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f,  %d)", tag, mpiRank, reqNum, input.temperature, input.density[0], input.density[1], input.density[2], input.density[3], input.charges[0], input.charges[1], input.charges[2], input.charges[3], input.masses[0], input.masses[1], input.masses[2], input.masses[3], reqType);
	std::string retString(sqlBuf);
	return retString;
}
template <> std::string getReqSQLString<lbmToOneDMD_request_t>(lbmToOneDMD_request_t input, int mpiRank, char * tag, int reqNum, unsigned int reqType)
{
	exit(1);
}

/**
 * @brief Get SELECT string for range of results by request IDs
 *
 * @tparam T Type of result
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param reqRange Tuple of ints corresponding to inclusive range of request IDs
 * @return std::string SQL select command for range of results or error for unsupported type
 */
template <typename T> std::string getResultSQLStringReqRange(int mpiRank, char * tag, std::tuple<int,int> reqRange)
{
	exit(1);
}
template <> std::string getResultSQLStringReqRange<bgk_result_t>(int mpiRank, char * tag, std::tuple<int,int> reqRange)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "SELECT * FROM BGKRESULTS WHERE REQ>=%d AND REQ <=%d  AND TAG=\'%s\' AND RANK=%d;", std::get<0>(reqRange), std::get<1>(reqRange), tag, mpiRank);
	std::string retString(sqlBuf);
	return retString;
}

/**
 * @brief Get SELECT string for single result by request IDs
 *
 * @tparam T Type of result
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param reqNum ID of request
 * @return std::string SQL select command for single result or error for unsupported type
 */
template <typename T> std::string getResultSQLString(int mpiRank, char * tag, int reqNum)
{
	exit(1);
}
template <> std::string getResultSQLString<bgk_result_t>(int mpiRank, char * tag, int reqNum)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "SELECT * FROM BGKRESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNum, tag, mpiRank);
	std::string retString(sqlBuf);
	return retString;
}
template <> std::string getResultSQLString<bgkmasses_result_t>(int mpiRank, char * tag, int reqNum)
{
	char sqlBuf[2048];
	sprintf(sqlBuf, "SELECT * FROM BGKMASSESRESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNum, tag, mpiRank);
	std::string retString(sqlBuf);
	return retString;
}
template <> std::string getResultSQLString<lbmToOneDMD_result_t>(int mpiRank, char * tag, int reqNum)
{
	exit(1);
}

/**
 * @brief Insert fine grain simulation request into GLUE Code
 *
 * @tparam T The type of the request
 * @param input The request itself
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param dbHandle Database to write to
 * @param reqNum ID of request
 * @param reqType ALInterfaceMode_e of request type
 */
template <typename T> void writeRequest(T input, int mpiRank, char * tag, dbHandle_t  dbHandle, int reqNum, unsigned int reqType)
{
	std::string sqlString = getReqSQLString<T>(input, mpiRank, tag, reqNum, reqType);
	sendSQLCommand<T>(sqlString, dbHandle);
	return;
}

/**
 * @brief Read specific request ID and block until data is available
 *
 * @tparam T Type of result
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param dbHandle Database to write to
 * @param reqNum ID of request
 * @param reqType ALInterfaceMode_e of request type
 * @return T Result from database
 */
template <typename T> T readResult_blocking(int mpiRank, char * tag, dbHandle_t  dbHandle, int reqNum, unsigned int reqType)
{
	T retVal;
	char sqlBuf[2048];
	char *err = nullptr;
	//Spin on file until result is available
	bool haveResult = false;
	if(reqType == ALInterfaceMode_e::KILL)
	{
		haveResult = true;
	}

	while(!haveResult)
	{
		//Send SELECT
		std::string sqlString = getResultSQLString<T>(mpiRank, tag, reqNum);
		sendSQLCommand<T>(sqlString, dbHandle);

		//SQL did something, so Get table
		auto globalTable = getGlobalTable<T>();

		//And get lock
		globalTable.tableMutex.lock();
		//Check if result in table
		auto res = globalTable.resultTable.find(reqNum);
		if (res != globalTable.resultTable.end())
		{
			//It exists, so this is the final iteration of the loop
			haveResult = true;
			retVal = res->second;
		}
		//Relase lock
		globalTable.tableMutex.unlock();
	}

	return retVal;
}

/**
 * @brief Request a single fine grain simulation with specified request type
 *
 * @tparam S Type of request
 * @tparam T Type of expected result
 * @param input 
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param dbHandle Database to write to
 * @param reqType ALInterfaceMode_e of request type
 * @return T Result of simulation
 */
template <typename S, typename T> T req_single_with_reqtype(S input, int mpiRank, char * tag, dbHandle_t dbHandle, unsigned int reqType)
{
	int reqNumber = getReqNumber();

	T retVal;

	//Send request
	writeRequest<S>(input, mpiRank, tag, dbHandle, reqNumber, reqType);

	//Read result
	retVal = readResult_blocking<T>(mpiRank, tag, dbHandle, reqNumber, reqType);

	return retVal;
}

/**
 * @brief Batch request of fine grain simulations with specified request type
 *
 * @tparam S Type of request
 * @tparam T Type of expected result
 * @param input Array of requests of type S
 * @param numInputs Length of input array
 * @param mpiRank MPI Rank of requesting process
 * @param tag Tag corresponding to set of requests
 * @param dbHandle Database to write to
 * @param reqType ALInterfaceMode_e of request type
 * @return T* Array of results of length numInputs
 */
template <typename S, typename T> T* req_batch_with_reqtype(S *input, int numInputs, int mpiRank, char * tag, dbHandle_t  dbHandle, unsigned int reqType)
{
	std::set<int> reqQueue;
	T * retVal = (T *)malloc(sizeof(T) * numInputs);
	//Start all requests
	for(int i = 0; i < numInputs; i++)
	{
		int reqNumber = getReqNumber();
		writeRequest<S>(input[i], mpiRank, tag, dbHandle, reqNumber, reqType);
		reqQueue.insert(reqNumber);
	}

	//Process requests
	//In this case we block on each request so it is pretty simple
	int retValCounter = 0;
	for(auto curReq = reqQueue.begin(); curReq != reqQueue.end(); curReq++)
	{
		retVal[retValCounter] = readResult_blocking<T>(mpiRank, tag, dbHandle, *curReq, reqType);
		retValCounter++;
	}

	return retVal;
}

/**
 * @brief Insert batch requests as an MPI collective operation
 *
 * @tparam T Type of request
 * @param input Array of requests of type S
 * @param numInputs Length of input array
 * @param reqRank MPI Rank of requesting process
 * @param dbHandle Database to write to
 * @return std::unique_ptr<std::vector<int>> 
 */
template<typename T> std::unique_ptr<std::vector<int>> col_insertReqs(T *input, int numInputs, int reqRank, dbHandle_t  dbHandle)
{
	//Return a full vector as we have no guarantee of contiguous reqIDs
	auto retVec = std::make_unique<std::vector<int>>(numInputs, -1);
	std::string tag("TAG");
	int start,end;
	int reqNum;
	for(int i = 0; i < numInputs; i++)
	{
		reqNum = getReqNumberForRank(reqRank);
		(*retVec)[i] = reqNum;
		///TODO: Remove "TAG" requirement
		writeRequest<T>(input[i], reqRank, const_cast<char *>(tag.c_str()), dbHandle, reqNum, ALInterfaceMode_e::DEFAULT);
	}
	return retVec;
}

/**
 * @brief Helper function to request a range of results to support batch requests
 *
 * @tparam T Type of result
 * @param nextID The lowest ID of the block of requests. Inclusive
 * @param maxID The maximum ID of the block of requests. Inclusive
 * @param mpiRank MPI Rank of requesting process
 * @param dbHandle Database to write to
 * @param reqType ALInterfaceMode_e of request type
 * @return std::unique_ptr<std::vector<std::tuple<int, T>>> Vector of tuples of request IDs and results
 */
template <typename T> std::unique_ptr<std::vector<std::tuple<int, T>>> getRangeOfResults(int nextID, int maxID, int mpiRank, dbHandle_t dbHandle, unsigned int reqType)
{
	auto retVec = std::make_unique<std::vector<std::tuple<int,T>>>();
	//Put request IDs in a tuple
	std::tuple<int,int> reqRange(nextID, maxID);
	std::string tag("TAG");
	char sqlBuf[2048];
	char *err = nullptr;
	//Spin on file until result is available
	bool haveResult = false;
	if(reqType == ALInterfaceMode_e::KILL)
	{
		haveResult = true;
	}

	///NOTE: This seems to be the start chunk?
	while(!haveResult)
	{
		//Send SELECT
		std::string sqlString = getResultSQLStringReqRange<T>(mpiRank, const_cast<char *>(tag.c_str()), reqRange);
		sendSQLCommand<T>(sqlString, dbHandle);

		//SQL did something, so Get table
		auto globalTable = getGlobalColTable<T>(mpiRank);
		//And get lock (less needed in this mode)
		globalTable.tableMutex.lock();
		//Check if any results we want are in table
		auto it = globalTable.resultTable.begin();
		while(it != globalTable.resultTable.end())
		{
			if(it->first <= maxID || it->first >= nextID)
			{
				//Hit so copy it out...
				std::tuple<int, T> retTup(it->first, it->second);
				retVec->push_back(retTup);
				//and remove it
				it = globalTable.resultTable.erase(it);
				//And we have at least one result so
				haveResult = true;
			}
			else
			{
				++it;
			}
		}
		//Relase lock
		globalTable.tableMutex.unlock();
	}
	return retVec;
}

/**
 * @brief Helper function to process and order batch results
 *
 * @tparam T Type of result
 * @param reqList Reference to vector of request IDs
 * @param reqRank MPI Rank of requesting process
 * @param dbHandle Database to write to
 * @return std::vector<T>* Pointer to vector of results
 */
template <typename T> std::vector<T> * col_extractResults(std::unique_ptr<std::vector<int>> &reqList, int reqRank, dbHandle_t dbHandle)
{
	///TODO: Consider thought to reducing memory footprint because we can potentially use 2N for this
	std::vector<T> * retVec = new std::vector<T>(reqList->size());

	//We have guarantee that reqRange[0] is lowest ID but not that all IDs are contiguous
	//Need to request lowest to max until all results have been received

	// Start by requesting the full range
	int rStart, rEnd;
	rStart = *(reqList->begin());
	rEnd = reqList->back();
	bool isDone = false;

	while(!isDone)
	{
		//Assume we are done until we aren't
		isDone = true;
		///TODO: Use logic to update rStart and rEnd to make smaller requests as time goes on
		//Get results of query
		auto sqlResults = getRangeOfResults<T>(rStart, rEnd, reqRank, dbHandle, ALInterfaceMode_e::DEFAULT);
		if(!sqlResults->empty())
		{
			//Basically look for matches between the two vectors in a not horrible way
			//  Probably O(N^2)...
			for(int i = 0; i < reqList->size(); i++)
			{
				//Have we processed this request yet?
				if(reqList->at(i) != -1)
				{
					//Nope, so let's see if our sqlResults have a corresponding entry
					auto matchIter = std::find_if(
						sqlResults->begin(), sqlResults->end(),
						[&](const std::tuple<int, T>& x) { return std::get<0>(x) == reqList->at(i);}
					);
					if(matchIter != sqlResults->end())
					{
						//We have a hit so copy out the request and set the reqList entry to -1
						retVec->at(i) = std::get<1>(*matchIter);
						reqList->at(i) = -1;
					}
					else
					{
						//Otherwise, no hit and we need to try again
						isDone = false;
					}
				}
			}
		}
		else
		{
			isDone = false;
		}
	}
	return retVec;
}

/**
 * @brief (MPI) Collective Batch Request of fine grain simulations
 *
 * @tparam S Type of request
 * @tparam T Type of expected result
 * @param input Array of requests of type S
 * @param numInputs Length of input array
 * @param glueComm MPI Communicator to use with GLUE Library
 * @return T* local array of length numInputs containing results
 */
template <typename S, typename T> T* req_collective(S *input, int numInputs, MPI_Comm glueComm)
{
	//Thanks to Andrew Reisner for helping with a lot of the thought process behind the MPI aspects of the algorithm
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
	T* resultsBuffer = static_cast<T*>(malloc(sizeof(T) * numInputs));
	//If rank 0
	if(myRank == 0)
	{
		std::vector<int> resultBatches(reqBatches);
		//A vector of queues of unique pointers of vectors of request ID mappings
		std::vector<  std::queue< std::unique_ptr<std::vector<int>>>> reqsPerBatch(commSize);
		//First, submit all rank 0 requests
		auto zeroReqs = col_insertReqs<S>(input, numInputs, 0, globalGlueDBHandle);
		reqsPerBatch[0].push(std::move(zeroReqs));
		//And we know we have one batch for zero because it is special
		resultBatches[0] = 1;
		//Then, do the rest
		std::vector<S> reqs(globalGlueBufferSize);
		for(int rank = 1; rank < commSize; rank++)
		{
			//Do we still have requests from that rank?
			while(reqBatches[rank] != 0)
			{
				//Blocking recv those requests
				MPI_Status reqStatus;
				//MPI IDs decrement [total, 1]
				MPI_Recv(reqs.data(), globalGlueBufferSize*sizeof(S), MPI_BYTE, rank, reqBatches[rank], glueComm, &reqStatus);
				//And determine how many were actually sent to us
				int numReqs;
				MPI_Get_count(&reqStatus, MPI_BYTE, &numReqs);
				numReqs = numReqs / sizeof(S);
				//Send to glue code
				auto batchRange  = col_insertReqs<S>(reqs.data(), numReqs, rank, globalGlueDBHandle);
				// Put requests in req list
				//   Because of Choices, batch N is in reqBatches[0] and 0 is in reqBatches[N-1]
				//   What we actually want is a FIFO?
				reqsPerBatch[rank].push(std::move(batchRange));
				//And decrement the number of expected batches from this rank
				reqBatches[rank]--;
			}
		}
		//Now, we process results
		for(int rank = 1; rank < commSize; rank++)
		{
			//Do we still have results for that rank?
			while(resultBatches[rank] != 0)
			{
				int batchNum = resultBatches[rank];
				//Get results from glue code
				auto reqIDVec = std::move(reqsPerBatch[rank].front());
				reqsPerBatch[rank].pop();
				std::vector<T> * batchResults = col_extractResults<T>(reqIDVec, rank, globalGlueDBHandle);
				//Send results with a BLOCKING send
				// Need to do blocking sends because of memory concerns
				//MPI IDs decrement [total, 1]
				MPI_Send(batchResults->data(), batchResults->size()*sizeof(T), MPI_BYTE, rank, resultBatches[rank], glueComm); 
				//Free memory
				delete batchResults;
				//And decrement result batches counter
				resultBatches[rank]--;
			}
		}
		//And then handle the requests from rank 0
		auto reqIDVec = std::move(reqsPerBatch[0].front());
		reqsPerBatch[0].pop();
		std::vector<T> * batchResults = col_extractResults<T>(reqIDVec, 0, globalGlueDBHandle);
		std::copy(batchResults->begin(), batchResults->end(), resultsBuffer);
		delete batchResults;
	}
	else
	{
		//Everyone else, send your requests to rank 0
		unsigned int curIndex = 0;
		std::vector<MPI_Request> sendReqs(localReqBatches[myRank]);
		std::vector<MPI_Status> sendStatuses(localReqBatches[myRank]);
		for(int i = localReqBatches[myRank]; i > 0; i--)
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
			MPI_Isend(&input[curIndex], sizeof(S)*reqSize, MPI_BYTE, 0, i, glueComm, &sendReqs[i-1]);
			//Increment curIndex
			curIndex += globalGlueBufferSize;
		}
		//Wait on all the sends
		MPI_Waitall(localReqBatches[myRank], sendReqs.data(), sendStatuses.data());
		//Then get results
		curIndex = 0;
		std::vector<MPI_Request> recvReqs(localReqBatches[myRank]);
		std::vector<MPI_Status> recvStatuses(localReqBatches[myRank]);
		for(int i = localReqBatches[myRank]; i > 0; i--)
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
			MPI_Irecv(&resultsBuffer[curIndex], sizeof(T)*reqSize, MPI_BYTE, 0, i, glueComm, &recvReqs[i-1]);
			//Increment curIndex
			curIndex += globalGlueBufferSize;
		}
		MPI_Waitall(localReqBatches[myRank], recvReqs.data(), recvStatuses.data());
	}
	//Return results
	return resultsBuffer;
}

/**
 * @brief Comparator for request IDs for sorting purposes
 *
 * @tparam T Type of data associated with ID
 * @param lhs First Tuple 
 * @param rhs Second tuple
 * @return true if lhs < rhs
 * @return false if rhs < lhs
 */
template <typename T> bool reqIDMin(std::tuple<int, T> lhs, std::tuple<int, T> rhs)
{
	int lhsID = std::get<0>(lhs);
	int rhsID = std::get<0>(rhs);
	if(lhsID < rhsID)
	{
		return true;
	}
	else
	{
		return false;
	}
}

#endif /* __alInterface_hpp */
