module alinterface_f
	use, intrinsic :: iso_c_binding
	implicit none

	public

	type, bind(c) :: lbmToOneDMD_request_f
		real(c_double) :: distance
		real(c_double) :: density
		real(c_double) :: temperature
		integer(c_int) :: provenance
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

	type, bind(c) :: bgk_request_f
		real(c_double) :: temperature
		real(c_double) :: density(4)
		real(c_double) :: charges(4)
		integer(c_int) :: provenance
	end type bgk_request_f

	type, bind(c) :: bgk_result_f
		real(c_double) :: viscosity
		real(c_double) :: thermalConductivity
		real(c_double) :: diffusionCoefficient(10)
	end type bgk_result_f

	enum, bind(c)
		enumerator :: LAMMPS = 0
		enumerator :: ACTIVELEARNER = 2
		enumerator :: FAKE = 3
		enumerator :: DEFAULT = 4
		enumerator :: FASTLAMMPS = 5
		enumerator :: KILL = 9
	end enum

contains

function lbmToOneDMD_req_single(input, mpiRank, tag, dbHandle) bind(c,name="lbmToOneDMD_req_single") result(res)
	use iso_c_binding
	type(lbmToOneDMD_request_f), value :: input
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr), value :: dbHandle
	type(lbmToOneDMD_result_f) :: res
end function lbmToOneDMD_req_single

function bgk_req_single(input, mpiRank, tag, dbHandle) bind(c,name="bgk_req_single") result(res)
	use iso_c_binding
	type(bgk_request_f), value :: input
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr), value :: dbHandle
	type(bgk_result_f) :: res
end function bgk_req_single

function bgk_req_batch_internal(input, numInputs, mpiRank, tag, dbHandle) bind(c,name="bgk_req_batch") result(res)
	use iso_c_binding
	type(bgk_request_f) :: input(numInputs)
	integer(c_int), value :: numInputs
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr), value :: dbHandle
	type(c_ptr) res
end function bgk_req_batch_internal

function bgk_req_batch(input, numInputs, mpiRank, tag, dbHandle) result(res)
	use iso_c_binding
	type(bgk_request_f) :: input(numInputs)
	integer(c_int), value :: numInputs
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr), value :: dbHandle
	type(c_ptr) intermediate
	type(bgk_result_f), pointer :: res(:)

	! TODO: Verify this kludge is safe
	intermediate = bgk_req_batch_internal(input, numInputs, mpiRank, tag, dbHandle)
	call c_f_pointer(intermediate, res, [numInputs])
end function bgk_req_batch

function initDB(mpiRank,fName) bind(c,name="initDB") result(dbhandle) 
	use iso_c_binding
	type(c_ptr) :: dbhandle
	integer(c_int), value :: mpiRank
	character(kind=c_char)  :: fName(*)
end function initDB

subroutine lbmToOneDMD_stop_service(mpiRank, tag, dbHandle) bind(c, name="lbmToOneDMD_stop_service")
	use iso_c_binding
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr) :: dbhandle
end subroutine lbmToOneDMD_stop_service

subroutine bgk_stop_service(mpiRank, tag, dbHandle) bind(c, name="bgk_stop_service")
	use iso_c_binding
	integer(c_int), value :: mpiRank
	character(kind=c_char) :: tag(*)
	type(c_ptr) :: dbhandle
end subroutine bgk_stop_service

subroutine resFreeWrapper(buffer) bind(c, name="resFreeWrapper")
	use iso_c_binding
	type(c_ptr) :: buffer
end subroutine resFreeWrapper

end module alinterface_f