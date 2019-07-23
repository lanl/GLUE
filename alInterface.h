#ifndef __alInterface_h
#define __alInterface_h

#include <sqlite3.h>

struct icf_request_s
{
	double temperature;
	//n
	double density[4];
	double charges[4];
};

struct icf_result_s
{
	double viscosity;
	double thermalConductivity;
	//n*n+1/2
	double diffusionCoefficient[10];
};

typedef struct icf_result_s icf_result_t;
typedef struct icf_request_s icf_request_t;

#ifdef __cplusplus
extern "C"
{
#endif
	icf_result_t icf_req_single(icf_request_t input, int mpiRank, char * tag, sqlite3 *dbHandle);
	icf_result_t* icf_req_batch(icf_request_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle);
	sqlite3 * initDB(int mpiRank, char * fName);
	void closeDB(sqlite3* dbHandle);
#ifdef __cplusplus
}
#endif

#endif /* __alInterface_h */