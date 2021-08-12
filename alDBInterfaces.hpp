#ifndef __alDBInterfaces_hpp
#define __alDBInterfaces_hpp

#include "alInterface.h"
#include <sqlite3.h>
#include <string>

void sendWriteRequest(std::string &sqlString, sqlite3 * dbHandle);

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

#endif /* __alDBInterfaces_hpp */
