#include "alInterface.h"
#include <stdlib.h>
#include <stdio.h>

struct GridPoint_s
{
	double val;
	double left;
	double right;
};
typedef struct GridPoint_s GridPoint_t;

const unsigned int dimX = 16;
const unsigned int nSteps = 2;
const double tolerance = 0.001;


int main(int argc, char ** argv)
{
	char * fName = "testDB.db";
	char * tag = "DUMMY_TAG_42";

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
	GridPoint_t expected[dimX];
	for(int i = 0; i < dimX; i++)
	{
		expected[i].val = 0.0;
		if(i == dimX/2)
		{
			expected[i].val = 100.0;
		}
	}

	int provenanceError = 0;

	//Initialize DB
	dbHandle_t dbHandle = initDB(0, fName);

	//Timesteps
	for(int t = 0; t < nSteps; t++)
	{
		//Prepare arguments
		for(int i = 0; i < dimX; i++)
		{
			if(i == 0)
			{
				grid[i].left = grid[dimX-1].val;
				expected[i].left = expected[dimX-1].val;
			}
			else
			{
				grid[i].left = grid[i-1].val;
				expected[i].left = expected[i-1].val;
			}
			if(i == dimX-1)
			{
				grid[i].right = grid[0].val;
				expected[i].right = expected[0].val;
			}
			else
			{
				grid[i].right = grid[i+1].val;
				expected[i].right = expected[i+1].val;
			}
		}
		bgk_request_t input[dimX];
		for(int i = 0; i < dimX; i++)
		{
			input[i].temperature = grid[i].val;
			input[i].density[0] = grid[i].left;
			for(int j = 1; j < 4; j++)
			{
				input[i].density[j] = 7.2;
			}
			input[i].charges[3] = grid[i].right;
			for(int j = 0; j < 3; j++)
			{
				input[i].charges[j] = 2.7;
			}
		}

		//Update state
		//Individual
		for(int i = 0; i < dimX/2; i++)
		{
			//Individual
			bgk_result_t result = bgk_req_single(input[i], 0, tag, dbHandle);
			if(result.provenance != FAKE)
			{
				provenanceError = 1;
			}
			grid[i].val =  result.diffusionCoefficient[7];
		}
		//Batch
		bgk_result_t *result = bgk_req_batch(&input[dimX/2], dimX/2, 0, tag, dbHandle);
		for(int i = 0; i < dimX/2; i++)
		{
			grid[i+dimX/2].val =  result[i].diffusionCoefficient[7];
			if(result[i].provenance != FAKE)
			{
				provenanceError = 1;
			}
		}
		free(result);
		//Control
		for(int i = 0; i < dimX; i++)
		{
			expected[i].val = (expected[i].right + expected[i].val + expected[i].left) / 3;
		}
	}

	//Compare
	int retVal;
	double diff = 0.0;
	for(int i = 0; i < dimX; i++)
	{
		diff += expected[i].val - grid[i].val;
	}
	if(diff > tolerance)
	{
		fprintf(stderr, "Error: Diff > Tolerance\n");
		retVal = 1;
	}
	else
	{
		retVal = 0;
	}

	if(provenanceError != 0)
	{
		fprintf(stderr, "Error: Provenance is too real\n");
		retVal = 1;
	}

	//Terminate Service
	bgk_stop_service(0, tag, dbHandle);

	//Close DB
	closeDB(dbHandle);

	return retVal;
}