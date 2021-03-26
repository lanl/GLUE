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

	int glueRank, glueSize;
	MPI_Comm_rank(glueComm, &glueRank);
	MPI_Comm_size(glueComm, &glueSize);

	char npFName[128];
	sprintf(npFName, "%d_%d_mpi.dat", glueSize, numReqs);

	//Set up buffer with rank specific data
	bgk_request_t * reqBuffer = malloc(sizeof(bgk_request_t) * numReqs);
	for(int i = 0; i < numReqs; i++)
	{
		reqBuffer[i].temperature = 160 + 10 * i * (glueRank + 1);
		reqBuffer[i].density[0] = 4.44819405e+24;
		reqBuffer[i].density[1] = 4.44819405e+24;
		reqBuffer[i].density[2] = 0.0;
		reqBuffer[i].density[3] = 0.0;
		reqBuffer[i].charges[0] = 0.9308375079943152;
		reqBuffer[i].charges[1] = 11.544522277358098;
		reqBuffer[i].charges[2] = 0.0;
		reqBuffer[i].charges[3] = 0.0;
	}
	for(int t = 0; t < numSteps; t++)
	{
		//And send buffer
		double start = MPI_Wtime();
		bgk_result_t* result = icf_req(reqBuffer, numReqs, glueComm);
		double end = MPI_Wtime();
		double secs = end - start;
		double msecs = secs * 1000;
		printf("%d: %ld millisecs\n", t, msecs);
		//We actually DO care about results right now so check that
		for(int r = 0; r < glueSize; r++)
		{
			MPI_Barrier(glueComm);
			if(glueRank == r)
			{
				//Print data
				for(int i = 0; i < numReqs; i++)
				{
					fprintf(stdout, "[%d,%d] : ", r, i);
					//Print request
					fprintf(stdout, "BGKInputs(");
					fprintf(stdout,"Temperature=%f, ", reqBuffer[i].temperature);
					fprintf(stdout, "Density=[%.8e, %.8e, %.8e, %.8e], ", reqBuffer[i].density[0], reqBuffer[i].density[1], reqBuffer[i].density[2], reqBuffer[i].density[3]);
					fprintf(stdout, "Charges=[%.8e, %.8e, %.8e, %.8e]", reqBuffer[i].charges[0], reqBuffer[i].charges[1], reqBuffer[i].charges[2], reqBuffer[i].charges[3]);
					fprintf(stdout, ")");
					//Print divider
					fprintf(stdout, " -> ");
					//Print result
					fprintf(stdout, "BGKOutputs(");
					fprintf(stdout, "Viscosity=%f, ", result[i].viscosity);
					fprintf(stdout, "ThermalConductivity=%f, ", result[i].thermalConductivity);
					fprintf(stdout, "DiffCoeff=[");
					for(int j = 0; j < 10; j++)
					{
						fprintf(stdout, "%f",  result[i].diffusionCoefficient[j]);
						if(j != 9)
						{
							fprintf(stdout, ", ");
						}
					}
					fprintf(stdout, "]");
					fprintf(stdout, ")");
					//Print endline
					fprintf(stdout, "\n");
				}
				//Only fake numpy for the first timestep
				if(t == 0)
				{
					FILE * fp = fopen(npFName, "a");
					for(int i = 0; i < numReqs; i++)
					{
						//Row ID
						fprintf(fp, "%d %d ", r, i);
						// Input
						fprintf(fp, "%.8e ", reqBuffer[i].temperature);
						for(int j = 0; j < 4; j++)
						{
							fprintf(fp, "%.8e ", reqBuffer[i].density[j]);
						}
						for(int j = 0; j < 4; j++)
						{
							fprintf(fp, "%.8e ", reqBuffer[i].charges[j]);
						}
						//Output
						fprintf(fp, "%.8e %.8e ", result[i].viscosity, result[i].thermalConductivity);
						for(int j = 0; j < 10; j++)
						{
							fprintf(fp, "%.8e", result[i].diffusionCoefficient[j]);
							if(j != 9)
							{
								fprintf(fp, " ");
							}
						}
						fprintf(fp, "\n");
					}
					fclose(fp);
				}
			}
		}
		//And we don't care about result because it probably worked
		free(result);
		//Now update a variable so we can see if we did this correctly
		for(int i = 0; i < numReqs; i++)
		{
			reqBuffer[i].temperature += 0.01 * i * (glueRank + 1);
		}
	}
	//Cleanup
	free(reqBuffer);

	//Terminate glue code
	closeGlue(glueComm);

	//Close MPI
	MPI_Finalize();

	return 0;
}
