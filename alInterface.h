#ifndef __alInterface_h
#define __alInterface_h

#include <sqlite3.h>

struct bgk_request_s
{
	double temperature;
	//n
	double density[4];
	double charges[4];
};

struct bgk_result_s
{
	double viscosity;
	double thermalConductivity;
	//n*n+1/2
	double diffusionCoefficient[10];
};

typedef struct bgk_result_s bgk_result_t;
typedef struct bgk_request_s bgk_request_t;

#ifdef __cplusplus
extern "C"
{
#endif
	bgk_result_t bgk_req_single(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle);
	bgk_result_t bgk_req_single_with_reqtype(bgk_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType);
	bgk_result_t* bgk_req_batch(bgk_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle);
	bgk_result_t* bgk_req_batch_with_reqtype(bgk_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle, unsigned int reqType);
	void bgk_stop_service(int mpiRank, char * tag, sqlite3 *dbHandle);
	sqlite3 * initDB(int mpiRank, char * fName);
	void closeDB(sqlite3* dbHandle);
#ifdef __cplusplus
}
#endif

#endif /* __alInterface_h */