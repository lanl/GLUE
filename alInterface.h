#ifndef __alInterface_h
#define __alInterface_h

#include <sqlite3.h>

struct InputStruct_s
{
	double density;
};

struct ResultStruct_s
{
	double density;
};

typedef struct ResultStruct_s ResultStruct_t;
typedef struct InputStruct_s InputStruct_t;

#ifdef __cplusplus
extern "C"
{
#endif
	ResultStruct_t reqFineGrainSim_single(InputStruct_s input, int mpiRank, char * tag, sqlite3 *dbHandle);
	ResultStruct_t* reqFineGrainSim_batch(InputStruct_s *input, int numInputs, int mpiRank, char * tag, sqlite3 *dbHandle);
#ifdef __cplusplus
}
#endif

#endif /* __alInterface_h */