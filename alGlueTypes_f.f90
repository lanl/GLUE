module algluetypes_f
	use, intrinsic :: iso_c_binding
	implicit none

	public

	type, bind(c) :: lbmToOneDMD_request_f
		real(c_double) :: distance
		real(c_double) :: density
		real(c_double) :: temperature
	end type lbmToOneDMD_request_f

	type, bind(c) :: lbmToOneDMD_result_f
		real(c_double) :: adsorption
	end type lbmToOneDMD_result_f

	type, bind(c) :: lbmDemo_request_f
		real(c_double) :: density
		integer(c_int) :: channelWidth
	end type lbmDemo_request_f

	type, bind(c) :: lbmDemo_result_f
		real(c_double) :: adsorption
		integer(c_int) :: provenance
	end type lbmDemo_result_f

	type, bind(c) :: bgk_request_f
		real(c_double) :: temperature
		real(c_double) :: density(4)
		real(c_double) :: charges(4)
	end type bgk_request_f

	type, bind(c) :: bgk_result_f
		real(c_double) :: viscosity
		real(c_double) :: thermalConductivity
		real(c_double) :: diffusionCoefficient(10)
		integer(c_int) :: provenance
	end type bgk_result_f

	enum, bind(c)
		enumerator :: LAMMPS = 0
		enumerator :: ACTIVELEARNER = 2
		enumerator :: FAKE = 3
		enumerator :: DEFAULT = 4
		enumerator :: FASTLAMMPS = 5
		enumerator :: KILL = 9
	end enum

end module algluetypes_f