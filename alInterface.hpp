#ifndef __alInterface_hpp
#define __alInterface_hpp

#include "alInterface.h"
#include <map>
#include <mutex>
#include <set>
#include <type_traits>
#include <string>

typedef icf_result_t SelectResult_t;

struct AsyncSelectTable_s
{
	std::map<int, SelectResult_t> resultTable;
	std::set<int> reqQueue;
	std::mutex tableMutex;
};

typedef struct AsyncSelectTable_s AsyncSelectTable_t;

extern AsyncSelectTable_t nastyGlobalSelectTable;

enum ALInterfaceMode_e
{
	LAMMPS = 0,
	MYSTIC = 1,
	ACTIVELEARNER = 2,
	FAKE = 3,
	DEFAULT = 4,
	KILL = 9
};

static int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName);

template <typename T> std::string getReqSQLString(T input, int mpiRank, char * tag, int reqNum, unsigned int reqType)
{
	char sqlBuf[2048];
	if(std::is_same<T, icf_request_t>::value)
	{
		sprintf(sqlBuf, "INSERT INTO REQS VALUES(\'%s\', %d, %d, %f, %f, %f, %f, %f, %f, %f, %f, %f, %d)", tag, mpiRank, reqNum, input.temperature, input.density[0], input.density[1], input.density[2], input.density[3], input.charges[0], input.charges[1], input.charges[2], input.charges[3], reqType);
	}
	std::string retString(sqlBuf);
	return retString;
}

template <typename T> void writeRequest(T input, int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum, unsigned int reqType)
{
	std::string sqlString = getReqSQLString<T>(input, mpiRank, tag, reqNum, reqType);
	int sqlRet;
	char *zErrMsg;
	sqlRet = sqlite3_exec(dbHandle, sqlString.c_str(), dummyCallback, 0, &zErrMsg);
	while( sqlRet != SQLITE_OK )
	{
		sqlRet = sqlite3_exec(dbHandle, sqlString.c_str(), dummyCallback, 0, &zErrMsg);
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

#endif /* __alInterface_hpp */