#include "alInterface.h"
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <sys/time.h>


int main(int argc, char ** argv)
{
	char * fName = "testDB.db";
	int numReqs = 2048;
	int numSteps = 4;

	struct timeval start, end;
	long mtime, secs, usecs;

	//Initialize MPI
	MPI_Init(&argc, &argv);

	//Set up problem size
	if(argc >= 2)
	{
		numReqs = atoi(argv[1]);
	}

	//Set up communicator
	///TODO
	//Connect to DB
	connectGlue(fName, MPI_COMM_WORLD);


	/*
	//Set up buffer
	bgk_request_t * reqBuffer = malloc(sizeof(bgk_request_t) * numReqs);
	for(int i = 0; i < numReqs; i++)
	{
		reqBuffer[i].temperature = 160 + 0.05 * i;
		reqBuffer[i].density[0] = 4.44819405e+24;
		reqBuffer[i].density[1] = 4.44819405e+24;
		reqBuffer[i].density[2] = 0.0;
		reqBuffer[i].density[3] = 0.0;
		reqBuffer[i].charges[0] = 0.9308375079943152;
		reqBuffer[i].charges[1] = 11.544522277358098;
		reqBuffer[i].charges[2] = 0.0;
		reqBuffer[i].charges[3] = 0.0;
	}

	for(int i = 0; i < numSteps; i++)
	{
		//And send buffer
		gettimeofday(&start, NULL);
		bgk_result_t *result = bgk_req_batch(reqBuffer, numReqs, 0, tag, dbHandle);
		gettimeofday(&end, NULL);
		secs  = end.tv_sec  - start.tv_sec;
		usecs = end.tv_usec - start.tv_usec;
		mtime = ((secs) * 1000 + usecs/1000.0) + 0.5;
		printf("%d: %ld millisecs\n", i, mtime);

		//And we don't care about result because it probably worked
		free(result);
	}

	//Cleanup
	free(reqBuffer);
	*/

	//Terminate glue code
	closeGlue(MPI_COMM_WORLD);

	//Close MPI
	MPI_Finalize();

	return 0;
}
