module alinterface_f
	use, intrinsic :: iso_c_binding
	use algluetypes_f
	implicit none

	public

	interface
		function lbmToOneDMD_req_single_f(input, mpiRank, tag, dbHandle) bind(c,name="lbmToOneDMD_req_single") result(res)
			use iso_c_binding
			use algluetypes_f
			type(lbmToOneDMD_request_f), value :: input
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr), value :: dbHandle
			type(lbmToOneDMD_result_f) :: res
		end function lbmToOneDMD_req_single_f
	end interface

	interface
		function bgk_req_single_f(input, mpiRank, tag, dbHandle) bind(c,name="bgk_req_single") result(res)
			use iso_c_binding
			use algluetypes_f
			type(bgk_request_f), value :: input
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr), value :: dbHandle
			type(bgk_result_f) :: res
		end function bgk_req_single_f
	end interface

	interface
		function bgk_req_batch_internal_f(input, numInputs, mpiRank, tag, dbHandle) bind(c,name="bgk_req_batch") result(res)
			use iso_c_binding
			use algluetypes_f
			type(bgk_request_f) :: input(numInputs)
			integer(c_int), value :: numInputs
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr), value :: dbHandle
			type(c_ptr) ::  res
		end function bgk_req_batch_internal_f
	end interface

	interface
		function initDB_f(mpiRank,fName) bind(c,name="initDB") result(dbhandle) 
			use iso_c_binding
			type(c_ptr) :: dbhandle
			integer(c_int), value :: mpiRank
			character(kind=c_char)  :: fName(*)
		end function initDB_f
	end interface

	interface
		subroutine lbmToOneDMD_stop_service_f(mpiRank, tag, dbHandle) bind(c, name="lbmToOneDMD_stop_service")
			use iso_c_binding
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr) :: dbhandle
		end subroutine lbmToOneDMD_stop_service_f
	end interface

	interface
		subroutine bgk_stop_service_f(mpiRank, tag, dbHandle) bind(c, name="bgk_stop_service")
			use iso_c_binding
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr), value :: dbhandle
		end subroutine bgk_stop_service_f
	end interface

	interface 
		subroutine resFreeWrapper_internal_f(buffer) bind(c, name="resFreeWrapper")
			use iso_c_binding
			type(c_ptr), value :: buffer
		end subroutine resFreeWrapper_internal_f
	end interface

	interface
		subroutine closeDB_f(dbHandle) bind(c, name="closeDB")
			use iso_c_binding
			type(c_ptr), value :: dbHandle
		end subroutine closeDB_f
	end interface

	contains

	function bgk_req_batch_f(input, numInputs, mpiRank, tag, dbHandle) result(res)
		use iso_c_binding
		type(bgk_request_f) :: input(numInputs)
		integer(c_int), value :: numInputs
		integer(c_int), value :: mpiRank
		character(kind=c_char) :: tag(*)
		type(c_ptr) :: dbHandle
		type(c_ptr) :: intermediate
		type(bgk_result_f), pointer :: res(:)

		! TODO: Verify this kludge is safe
		intermediate = bgk_req_batch_internal_f(input, numInputs, mpiRank, tag, dbHandle)
		call c_f_pointer(intermediate, res, [numInputs])
	end function bgk_req_batch_f

	subroutine bgk_req_batch_subr_f(input, output, numInputs, mpiRank, tag, dbHandle)
		use iso_c_binding
		type(bgk_request_f) :: input(numInputs)
		integer(c_int), value :: numInputs
		integer(c_int), value :: mpiRank
		character(kind=c_char) :: tag(*)
		type(c_ptr) :: dbHandle
		type(c_ptr) :: intermediateC
		type(bgk_result_f), pointer :: intermediateF(:)
		type(bgk_result_f), pointer :: output(:)

		! TODO: Verify this kludge is safe
		intermediateC = bgk_req_batch_internal_f(input, numInputs, mpiRank, tag, dbHandle)
		call c_f_pointer(intermediateC, intermediateF, [numInputs])
		output => intermediateF
	end subroutine bgk_req_batch_subr_f

	subroutine bgk_resFreeWrapper_f(ptr)
		use iso_c_binding
		type(bgk_result_f), pointer :: ptr(:)
		type(c_ptr) :: intermediate

		intermediate = c_loc(ptr)
		call resFreeWrapper_internal_f(intermediate)
	end subroutine bgk_resFreeWrapper_f

end module alinterface_f