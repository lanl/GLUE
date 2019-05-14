#ifndef __alInterface_h
#define __alInterface_h

#include <sqlite3.h>

const char * defaultTag = "THIS_IS_A_POC";

struct ResultStruct_s
{
	double density;
};

typedef struct ResultStruct_s ResultStruct_t;

ResultStruct_t reqFineGrainSim(double density, int mpiRank, char * tag, sqlite3 *dbHandle);


#endif /* __alInterface_h */