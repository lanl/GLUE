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

#ifdef __cplusplus
extern "C"
{
#endif
	ResultStruct_t reqFineGrainSim_single(InputStruct_s input, int mpiRank, char * tag, sqlite3 *dbHandle);
	void writeSelectResult(double density, int reqNum);
#ifdef __cplusplus
}
#endif

#endif /* __alInterface_h */