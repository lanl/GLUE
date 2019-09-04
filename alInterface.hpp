#ifndef __alInterface_hpp
#define __alInterface_hpp

#include "alInterface.h"
#include <map>
#include <mutex>
#include <set>

typedef icf_result_t SelectResult_t;

struct AsyncSelectTable_s
{
	std::map<int, SelectResult_t> resultTable;
	std::set<int> reqQueue;
	std::mutex tableMutex;
};

typedef struct AsyncSelectTable_s AsyncSelectTable_t;

extern AsyncSelectTable_t nastyGlobalSelectTable;

enum ALInterfaceMode_e
{
	LAMMPS = 0,
	MYSTIC = 1,
	ACTIVELEARNER = 2,
	FAKE = 3,
	DEFAULT = 4,
	KILL = 9
};

#endif /* __alInterface_hpp */