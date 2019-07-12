#ifndef __alInterface_h
#define __alInterface_h

#include <sqlite3.h>

struct InputStruct_s
{
	double temperature;
	//n
	double density[4];
	double charges[4];
};

struct ResultStruct_s
{
	double viscosity;
	double thermalConductivity;
	//n*n+1/2
	double diffusionCoefficient[10];
};

typedef struct ResultStruct_s ResultStruct_t;
typedef struct InputStruct_s InputStruct_t;

#ifdef __cplusplus
extern "C"
{
#endif
	ResultStruct_t reqFineGrainSim_single(InputStruct_t input, int mpiRank, char * tag, sqlite3 *dbHandle);
	ResultStruct_t* reqFineGrainSim_batch(InputStruct_t *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle);
	sqlite3 * initDB(int mpiRank, char * fName);
	void closeDB(sqlite3* dbHandle);
#ifdef __cplusplus
}
#endif

#endif /* __alInterface_h */