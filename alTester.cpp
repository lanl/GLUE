#include "alInterface.h"

int main(int argc, char ** argv)
{
	char * fName = "realTraining.db";
	char * tag = "makeMeOptionalAlready";

	//Initialize DB
	sqlite3 *dbHandle = initDB(0, fName);

	//Set up test cases
	///TODO: This is probably hard coded
	bgk_request_t requests[2];

	for(int i = 0; i < 2; i++)
	{
		//Do an AL BGK request
		bgk_result_t alReq = bgk_req_single_with_reqtype(requests[i], 0, tag, dbHandle, ALInterfaceMode_e::ACTIVELEARNER);

		//Do a LAMMPS BGK request
		bgk_result_t gndReq = bgk_req_single_with_reqtype(requests[i], 0, tag, dbHandle, ALInterfaceMode_e::LAMMPS);

		//Compare
		///TODO
	}

	//Terminate Service
	bgk_stop_service(0, tag, dbHandle);

	//Close DB
	closeDB(dbHandle);

	return 0;
}
