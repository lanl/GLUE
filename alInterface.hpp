#ifndef __alInterface_hpp
#define __alInterface_hpp

#include "alInterface.h"
#include <map>
#include <mutex>
#include <set>
#include <type_traits>
#include <string>

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
		///TODO: Address the mutex so we don't leave it locked
	}
};

extern AsyncSelectTable_t<icf_result_t> globalICFResultTable;

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
static int readCallback_icf(void *NotUsed, int argc, char **argv, char **azColName);

template <typename T> void * getResCallback()
{
	if(std::is_same<T, icf_request_t>::value)
	{
		return readCallback_icf;
	}
	else
	{
		return dummyCallback;
	}
}

template <typename T> AsyncSelectTable_t<T>& getGlobalTable()
{
	if(std::is_same<T, icf_request_t>::value)
	{
		return globalICFResultTable;
	}
	else
	{
		exit(1);
	}
}

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
	return;
}

template <typename T> T readResult(int mpiRank, char * tag, sqlite3 * dbHandle, int reqNum, unsigned int reqType)
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
		//Send SELECT with sqlite3_exec. 
		sprintf(sqlBuf, "SELECT * FROM RESULTS WHERE REQ=%d AND TAG=\'%s\' AND RANK=%d;", reqNum, tag, mpiRank);
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

#endif /* __alInterface_hpp */