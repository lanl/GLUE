#ifndef __alInterface_hpp
#define __alInterface_hpp

#include "alInterface.h"
#include <vector>
#include <mutex>

const char * defaultTag = "THIS_IS_A_POC";

typedef ResultStruct_t SelectResult_t;

struct AsyncSelectTable_s
{
	std::vector<SelectResult_t> resultTable;
	std::mutex tableMutex;
};

typedef struct AsyncSelectTable_s AsyncSelectTable_t;

extern AsyncSelectTable_t nastyGlobalSelectTable;

#endif /* __alInterface_hpp */