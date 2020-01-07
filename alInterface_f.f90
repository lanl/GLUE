module alinterface_f
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
	end type lbmDemo_result_f

	enum, bind(c)
		enumerator :: LAMMPS = 0
		enumerator :: MYSTIC = 1
		enumerator :: ACTIVELEARNER = 2
		enumerator :: FAKE = 3
		enumerator :: DEFAULT = 4
		enumerator :: FASTLAMMPS = 5
		enumerator :: KILL = 9
	end enum

contains

! TODO: Need to add handles to probably pass a c_ptr to sqlitedb
!   Idea being that we'll handle that on the C side to minimize fortran debugging
!     and maximize dryness
function lbmToOneDMD_req_single(input, mpiRank, tag, dbHandle) bind(c,name="lbmToOneDMD_req_single") result(res)
	use iso_c_binding
	type(lbmToOneDMD_request_f), value :: input
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr), value :: dbHandle
	type(lbmToOneDMD_result_f) :: res
end function lbmToOneDMD_req_single

function initDB(mpiRank,fName) bind(c,name="initDB") result(dbhandle) 
	use iso_c_binding
	type(c_ptr) :: dbhandle
	integer(c_int), value :: mpiRank
	character(kind=c_char)  :: fName(*)
end function initDB

end module alinterface_f