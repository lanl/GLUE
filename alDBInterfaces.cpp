#include "alDBInterfaces.hpp"
#include "alInterface.hpp"

void sendWriteRequest( std::string &sqlString, sqlite3 * dbHandle)
{
	char *zErrMsg = nullptr;
	int sqlRet = makeSQLRequest<void>(dbHandle, (char *)sqlString.c_str(), &zErrMsg);
	while( sqlRet != SQLITE_OK )
	{
		sqlRet = makeSQLRequest<void>(dbHandle, (char *)sqlString.c_str(), &zErrMsg);
		if(!(sqlRet == SQLITE_OK || sqlRet == SQLITE_BUSY || sqlRet == SQLITE_LOCKED))
		{
			fprintf(stderr, "Error in writeRequest<T>\n");
			fprintf(stderr, "SQL error %d: %s\n", sqlRet, zErrMsg);
			fprintf(stderr, "SQL Message: %s\n", sqlString.c_str());
			sqlite3_free(zErrMsg);
			sqlite3_close(dbHandle);
			exit(1);
		}
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

