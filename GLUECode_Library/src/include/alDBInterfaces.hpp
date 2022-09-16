#ifndef __alDBInterfaces_hpp
#define __alDBInterfaces_hpp

#include "alInterface.h"
#include <string>

#ifdef SOLVER_SIDE_SQLITE
#include <sqlite3.h>

int dummyCallback(void *NotUsed, int argc, char **argv, char **azColName);
int readCallback_bgk(void *NotUsed, int argc, char **argv, char **azColName);
int readCallback_colbgk(void *NotUsed, int argc, char **argv, char **azColName);

template <typename T> int makeSQLRequest(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, dummyCallback, 0, errOut);
}
template <> int makeSQLRequest<bgk_result_t>(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, readCallback_bgk, 0, errOut);
}

template <typename T> int makeColSQLRequest(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, dummyCallback, 0, errOut);
}
template <> int makeColSQLRequest<bgk_result_t>(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	return sqlite3_exec(dbHandle, message, readCallback_colbgk, 0, errOut);
}

template <typename T> void sendSQLCommand( std::string &sqlString, dbHandle_t  dbHandle)
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

#else
/**
 * @brief Helper Function to send an SQL Request to the GLUE Code
 *
 * @tparam T type used to indicate what type of data/tables should be used
 * @param dbHandle Database to communicate with
 * @param message Message/command to send
 * @param errOut Buffer to write errors to
 * @return int Return code from SQL library's command
 */
template <typename T> int makeSQLRequest(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	exit(1);
}
template <> int makeSQLRequest<bgk_result_t>(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	exit(1);
}

template <typename T> int makeColSQLRequest(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	exit(1);
}
template <> int makeColSQLRequest<bgk_result_t>(dbHandle_t  dbHandle, char * message, char ** errOut)
{
	exit(1);
}

/**
 * @brief Helper Function to send SQL Message to GLUE Code
 *
 * @tparam T type used to indicate what type of data/tables should be used
 * @param sqlString Message/command to send
 * @param dbHandle Database to communicate with
 */
template <typename T> void sendSQLCommand( std::string &sqlString, dbHandle_t  dbHandle)
{
	exit(1);
}

#endif

#endif /* __alDBInterfaces_hpp */
