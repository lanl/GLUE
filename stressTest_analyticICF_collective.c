#include "alInterface.h"
#include <mpi.h>
#include <stdlib.h>
#include <stdio.h>


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
	MPI_Comm glueComm;
	MPI_Comm_dup(MPI_COMM_WORLD, &glueComm);

	//Connect to DB
	connectGlue(fName, glueComm);

	int glueRank;
	MPI_Comm_rank(glueComm, &glueRank);

	//Set up buffer with rank specific data
	bgk_request_t * reqBuffer = malloc(sizeof(bgk_request_t) * numReqs);
	for(int i = 0; i < numReqs; i++)
	{
		reqBuffer[i].temperature = 160 + 0.05 * i * (glueRank + 1);
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
		double start = MPI_Wtime();
		bgk_result_t* result = icf_req(reqBuffer, numReqs, glueComm);
		double end = MPI_Wtime();
		double secs = end - start;
		double msecs = secs * 1000;
		printf("%d: %ld millisecs\n", i, msecs);

		///TODO: We actually DO care about results right now so check that
		//And we don't care about result because it probably worked
		free(result);
	}
	//Cleanup
	free(reqBuffer);

	//Terminate glue code
	closeGlue(glueComm);

	//Close MPI
	MPI_Finalize();

	return 0;
}
