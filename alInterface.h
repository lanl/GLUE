#ifndef __alInterface_h
#define __alInterface_h

struct ResultStruct_s
{
	double density;
};

typedef struct ResultStruct_s ResultStruct_t;

ResultStruct_t reqFineGrainSim(double density, int mpiRank);


#endif /* __alInterface_h */