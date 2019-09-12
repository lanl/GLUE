#include <stdio.h>
#include <string.h>

#include "alInterface.h"

const unsigned int dimX = 16;
const unsigned int nSteps = 2;
const char * defaultFName = "testDB.db";
const char * defaultTag = "DUMMY_TAG_42";

struct GridPoint_s
{
	double val;
	double left;
	double right;
};
typedef struct GridPoint_s GridPoint_t;

int main(int argc, char ** argv)
{
	char fName[128];
	char tag[128];

	if(argc >1)
		strcpy(tag, argv[1]);
	else
		strcpy(tag, defaultTag);

	if(argc > 2)
		strcpy(fName, argv[2]);
	else
		strcpy(fName, defaultFName);

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

	//Timesteps
	for(int t = 0; t < nSteps; t++)
	{
		//Prepare arguments
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
		for(int i = 0; i < dimX; i++)
		{
			bgk_request_t input;
			input.temperature = grid[i].val;
			input.density[0] = grid[i].left;
			input.charges[3] = grid[i].right;
			bgk_result_t result = bgk_req_single(input, 0, tag, dbHandle);
			grid[i].val =  result.diffusionCoefficient[7];
		}
	}

	fprintf(stdout, "Results:\n[");
	for(int i = 0; i < dimX; i++)
	{
		fprintf(stdout, "%f", grid[i].val);
		if(i != dimX - 1)
		{
			fprintf(stdout,", ");
		}
	}
	fprintf(stdout, "]\n");
	fflush(stdout);

	bgk_stop_service(0, tag, dbHandle);

	closeDB(dbHandle);

	return 0;
}