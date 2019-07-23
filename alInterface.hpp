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

#endif /* __alInterface_hpp */