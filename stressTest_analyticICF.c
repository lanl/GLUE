#include "alInterface.h"
#include <stdlib.h>
#include <stdio.h>

#define NUM_REQS 2048
#define NUM_TSTEPS 4


int main(int argc, char ** argv)
{
	char * fName = "testDB.db";
	char * tag = "DUMMY_TAG_42";

	//Initialize DB
	sqlite3 *dbHandle = initDB(0, fName);

	//Set up buffer
	bgk_request_t reqBuffer[NUM_REQS];
	for(int i = 0; i < NUM_REQS; i++)
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

	for(int i = 0; i < NUM_TSTEPS; i++)
	{
		//And send buffer
		bgk_result_t *result = bgk_req_batch((bgk_request_t*)&reqBuffer, NUM_REQS, 0, tag, dbHandle);

		//And we don't care about result because it probably worked
		free(result);
	}

	//Terminate Service
	bgk_stop_service(0, tag, dbHandle);

	//Close DB
	closeDB(dbHandle);

	return 0;
}
