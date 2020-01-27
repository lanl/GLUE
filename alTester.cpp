#include "alInterface.h"
#include <cmath>
#include <iostream>

int main(int argc, char ** argv)
{
	const char * fName = "realTraining.db";
	const char * tag = "makeMeOptionalAlready";

	//Initialize DB
	sqlite3 *dbHandle = initDB(0, (char *)fName);

	//Set up test cases
	///TODO: This is probably hard coded
	bgk_request_t requests[2];

	for(int i = 0; i < 2; i++)
	{
		//Do an AL BGK request
		//  Do this first because we don't want to re-train with the LAMMPS request
		bgk_result_t alReq = bgk_req_single_with_reqtype(requests[i], 0, (char *)tag, dbHandle, ALInterfaceMode_e::ACTIVELEARNER);

		//Do a LAMMPS BGK request
		bgk_result_t gndReq = bgk_req_single_with_reqtype(requests[i], 0, (char *)tag, dbHandle, ALInterfaceMode_e::LAMMPS);

		//Compare
		std::cout << "IN: temperature=" << requests[i].temperature << std::endl;
		for(int j = 0; j < 4; j++)
		{
			std::cout << "IN: density[" << j << "]=" << requests[i].density[j] << std::endl;
		}
		for(int j = 0; j < 4; j++)
		{
			std::cout << "IN: charges[" << j << "]=" << requests[i].charges[j] << std::endl;
		}

		std::cout << "DIFF: viscosity=" << abs(alReq.viscosity - gndReq.viscosity) << std::endl;
		std::cout << "DIFF: thermalConductivity=" << abs(alReq.thermalConductivity - gndReq.thermalConductivity) << std::endl;
		for(int j = 0; j < 10; j++)
		{
			std::cout << "DIFF: diffusionCoefficient[" << j << "]=" << abs(alReq.diffusionCoefficient[j] - gndReq.diffusionCoefficient[j]) << std::endl;
		}
	}

	//Terminate Service
	bgk_stop_service(0, (char *)tag, dbHandle);

	//Close DB
	closeDB(dbHandle);

	return 0;
}
