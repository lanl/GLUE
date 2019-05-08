#include "alInterface.h"

#include <stdio.h>

ResultStruct_t reqFineGrainSim(double density, int mpiRank)
{
	//Static variables are dirty but this is an okay use
	static int reqNumber = 0;

	ResultStruct_t retVal;

	///COMMENT: Should probably just use redis or something that can better support parallelism
	/// Assuming that for now we don't mind ranks being serialized. If we can provide asynchrony in lookups
	///   then we can better aggregate them and detect redundant calls before we hammer the file system

	char reqName_buffer[64];
	//Generate fName
	sprintf(reqName_buffer, "fgsReq_%d_%d", mpiRank, reqNumber);
	//Open file for writing in format fgsReq_RANK_reqNumber
	FILE *reqHandle = fopen(reqName_buffer, "w");
	//Write tab delimited string of arguments
	///TODO: Verify max precision, possibly by writing as hex
	fprintf(reqHandle, "%f\n", density);
	//Close file
	fclose(reqHandle);

	//Generate new fName
	char ackName_buffer[64];
	sprintf(reqName_buffer, "fgsAck_%d_%d", mpiRank, reqNumber);

	//Spin on file until result is available
	int haveResult = 0;
	while(!haveResult)
	{
		//Check if fgsAck_RANK_reqNumber exists and open if it does
		FILE *ackHandle = fopen(ackName_buffer, "r");
		if(ackHandle != NULL)
		{
			//Read results
			///TODO: Solve situation of a partial write
			double outDensity;
			fscanf(ackHandle, "%lf", &outDensity);
			haveResult = 1;
			retVal.density = outDensity;
			//Close file
			fclose(ackHandle);
		}
		else
		{
			//Some form of wait so we don't completley destroy the file system
		}
	}

	//Increment request number
	reqNumber++;

	return retVal;
}