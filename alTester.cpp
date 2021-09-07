#include "alInterface.h"
#include <cmath>
#include <iostream>

int main(int argc, char ** argv)
{
	const char * fName = "testDB.db";
	const char * tag = "makeMeOptionalAlready";

	//Initialize DB
	dbHandle_tdbHandle = initDB(0, (char *)fName);

	//Set up test cases
	///TODO: This is probably hard coded
	bgk_request_t requests[3];

	{
		//This case is well within the range of what we expect to interpolate
		//T=100 n1=5.e+24 n2= 5.e+24   Z1=0.927, Z2=11.426
		int reqId = 0;
		requests[reqId].temperature = 100;
		requests[reqId].density[0] = 5e24;
		requests[reqId].density[1] = 5e24;
		requests[reqId].density[2] = 0.0;
		requests[reqId].density[3] = 0.0;
		requests[reqId].charges[0] = 0.927;
		requests[reqId].charges[1] = 11.426;
		requests[reqId].charges[2] = 0.0;
		requests[reqId].charges[3] = 0.0;
	}
	{
		//This case should hopefully result in a bit of extrapolation as it is on the edge of our training data
		//T=540 n1=7.e+24 n2= 3.e+24 Z1=0.957, Z2=12.68
		int reqId = 1;
		requests[reqId].temperature = 540;
		requests[reqId].density[0] = 7e24;
		requests[reqId].density[1] = 3e24;
		requests[reqId].density[2] = 0.0;
		requests[reqId].density[3] = 0.0;
		requests[reqId].charges[0] = 0.957;
		requests[reqId].charges[1] = 12.68;
		requests[reqId].charges[2] = 0.0;
		requests[reqId].charges[3] = 0.0;
	}
	{
		//And if this case doesn't require a LAMMPS call then something is wrong
		//T=1000 n1=5.e+24 n2= 5.e+24   Z1=0.971, Z2=14.17
		int reqId = 2;
		requests[reqId].temperature = 1000;
		requests[reqId].density[0] = 5e24;
		requests[reqId].density[1] = 5e24;
		requests[reqId].density[2] = 0.0;
		requests[reqId].density[3] = 0.0;
		requests[reqId].charges[0] = 0.971;
		requests[reqId].charges[1] = 14.17;
		requests[reqId].charges[2] = 0.0;
		requests[reqId].charges[3] = 0.0;
	}

	for(int i = 0; i < 3; i++)
	{
		//Do an AL BGK request
		//  Do this first because we don't want to re-train with the LAMMPS request
		bgk_result_t alReq = bgk_req_single_with_reqtype(requests[i], 0, (char *)tag, dbHandle, ALInterfaceMode_e::ACTIVELEARNER);

		//Do a LAMMPS BGK request
		bgk_result_t gndReq = bgk_req_single_with_reqtype(requests[i], 0, (char *)tag, dbHandle, ALInterfaceMode_e::FGS);

		//Compare
		std::cout << "IN: Case " << i << std::endl;
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
		std::cout << "PROVENANCE: AL=" << alReq.provenance << std::endl << std::endl;
	}

	//Terminate Service
	bgk_stop_service(0, (char *)tag, dbHandle);

	//Close DB
	closeDB(dbHandle);

	return 0;
}
