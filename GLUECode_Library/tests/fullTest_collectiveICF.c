#include "alInterface.h"
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char ** argv)
{
	char * fName = "testDB.db";
	const int numReqs = 16;

	//Initialize MPI
	MPI_Init(&argc, &argv);

	//Set up communicator
	MPI_Comm glueComm;
	MPI_Comm_dup(MPI_COMM_WORLD, &glueComm);

	//Connect to DB
	connectGlue(fName, glueComm);

	int glueRank, glueSize;
	MPI_Comm_rank(glueComm, &glueRank);
	MPI_Comm_size(glueComm, &glueSize);

	//Set up request buffers
	bgk_request_t * reqBuffer = malloc(sizeof(bgk_request_t) * numReqs);
	for(int i = 0; i < numReqs; i++)
	{
		reqBuffer[i].temperature = 160 + 10 * i;
		reqBuffer[i].density[0] = 4.44819405e+24;
		reqBuffer[i].density[1] = 4.44819405e+24;
		reqBuffer[i].density[2] = 0.0;
		reqBuffer[i].density[3] = 0.0;
		reqBuffer[i].charges[0] = 0.9308375079943152;
		reqBuffer[i].charges[1] = 11.544522277358098;
		reqBuffer[i].charges[2] = 0.0;
		reqBuffer[i].charges[3] = 0.0;
	}

	//And process it
	double start = MPI_Wtime();
	bgk_result_t* result = icf_req(reqBuffer, numReqs, glueComm);
	double end = MPI_Wtime();
	double secs = end - start;
	double msecs = secs * 1000;
	printf("%ld millisecs\n", msecs);

	//Terminate glue code
	closeGlue(glueComm);

	//Close MPI
	MPI_Finalize();

	return 0;
}

