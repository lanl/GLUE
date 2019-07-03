#include <iostream>

#include "alInterface.h"

const unsigned int dimX = 8;
const unsigned int nSteps = 2;
const char * fName = "testDB.db"
const char * tag = "DUMMY_TAG_42";

struct GridPoint_s
{
	double val;
	double left;
	double right;
};
typedef struct GridPoint_s GridPoint_t;

int main(int argc, char ** argv)
{

	//Initialize DB
	sqlite3 *dbHandle = initDB(0, fName);

	//Set up grid
	GridPoint_t grid[dimX];
	for(int i = 0; i < dimX; i++)
	{
		grid[i].val = 0.0;
		if(i == dimX/2)
		{
			grid[i].val = 100.0;
		}
	}

	for(int t = 0; t < nSteps; t++)
	{
		//prepare arguments
		for(int i = 0; i < dimX; i++)
		{
			if(i == 0)
			{
				grid[i].left = grid[dimX-1].val;
			}
			else
			{
				grid[i].left = grid[i-1].val;
			}

			if(i == dimX-1)
			{
				grid[i].right = grid[0].val;
			}
			else
			{
				grid[i].right = grid[i+1].val;
			}
		}

		//Update state
		for(int = 0; i < dimX; i++)
		{
			//ResultStruct_t reqFineGrainSim_single(InputStruct_s input, int mpiRank, char * tag, sqlite3 *dbHandle);
			InputStruct_t input;
			input.temperature = grid[i].val;
			input.density[0] = grid[i].left;
			input.charges[3] = grid[i].right;
			ResultStruct_t result = reqFineGrainSim_single(input, 0, tag, dbHandle);

			grid[i].diffusionCoefficient[7] = transportCoeff;
		}
	}

	std::cout << "Results:" << std::endl << "[";
	for(int i = 0; i < dimX; i++)
	{
		std::cout << grid[i];
		if(i != dimX - 1)
		{
			std::cout << ", ";
		}
	}
	std::cout << "]" << std::endl;

	return 0;
}