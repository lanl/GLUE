#ifndef __alDBInterfaces_hpp
#define __alDBInterfaces_hpp

#include "alInterface.h"
#include <sqlite3.h>
#include <string>

int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName);
int readCallback_bgk(void *NotUsed, int argc, char **argv, char **azColName);
int readCallback_colbgk(void *NotUsed, int argc, char **argv, char **azColName);

template <typename T> int makeSQLRequest(sqlite3 * dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, dummyCallback, 0, errOut);
}
template <> int makeSQLRequest<bgk_result_t>(sqlite3 * dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, readCallback_bgk, 0, errOut);
}

template <typename T> int makeColSQLRequest(sqlite3 * dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, dummyCallback, 0, errOut);
}
template <> int makeColSQLRequest<bgk_result_t>(sqlite3 * dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, readCallback_colbgk, 0, errOut);
}

template <typename T> void sendSQLCommand( std::string &sqlString, sqlite3 * dbHandle)
{
	char *zErrMsg = nullptr;
	int sqlRet = makeSQLRequest<T>(dbHandle, (char *)sqlString.c_str(), &zErrMsg);
	while( sqlRet != SQLITE_OK )
	{
		sqlRet = makeSQLRequest<T>(dbHandle, (char *)sqlString.c_str(), &zErrMsg);
		if(!(sqlRet == SQLITE_OK || sqlRet == SQLITE_BUSY || sqlRet == SQLITE_LOCKED))
		{
			fprintf(stderr, "Error in sendSQLCommand\n");
			fprintf(stderr, "SQL error %d: %s\n", sqlRet, zErrMsg);
			fprintf(stderr, "SQL Message: %s\n", sqlString.c_str());
			sqlite3_free(zErrMsg);
			sqlite3_close(dbHandle);
			exit(1);
		}
	}
}

#endif /* __alDBInterfaces_hpp */
