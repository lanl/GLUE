module alinterface_f
	use, intrinsic :: iso_c_binding
	implicit none

	type, bind(c) :: lbmZeroD_request_f
		real(c_double) :: distance
		real(c_double) :: density
		real(c_double) :: temperature
	end type lbmZeroD_request_f

	type, bind(c) :: lbmZeroD_result_f
		real(c_double) :: adsorption
	end type lbmZeroD_result_f

	enum, bind(c)
		enumerator :: LAMMPS = 0
		enumerator :: MYSTIC = 1
		enumerator :: ACTIVELEARNER = 2
		enumerator :: FAKE = 3
		enumerator :: DEFAULT = 4
		enumerator :: KILL = 9
	end enum

contains


end module alinterface_f