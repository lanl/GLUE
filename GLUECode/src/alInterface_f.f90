module alinterface_f
	use, intrinsic :: iso_c_binding
	use algluetypes_f
	implicit none

	public

	!> Fortran interface to lbmToOneDMD_req_single()
	!! @param input Array of request of length numInputs
	!! @param mpiRank MPI Rank of requesting process
	!! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	!! @return res TODO
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

	!> Fortran interface to bgk_req_single()
	!! @param input Array of request of length numInputs
	!! @param mpiRank MPI Rank of requesting process
	!! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	!! @return res TODO
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

	!> Fortran interface to bgk_req_batch()
	!! @param input Array of request of length numInputs
	!! @param numInputs Length of input array
	!! @param mpiRank MPI Rank of requesting process
	!! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	!! @return res Array of results of length numInputs
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

    !> Fortran interface to initDB()
    !! This is a Fortran function that is used to initialize the SQLite database
    !! @param mpiRank MPI Rank of requesting process
    !! @param fName Field name
	!! @return dbHandle Database to write to
	interface
		function initDB_f(mpiRank,fName) bind(c,name="initDB") result(dbhandle) 
			use iso_c_binding
			type(c_ptr) :: dbHandle
			integer(c_int), value :: mpiRank
			character(kind=c_char)  :: fName(*)
		end function initDB_f
	end interface

    !> Fortran interface to lbmToOneDMD_stop_service()
    !! This is a Fortran function that is used to terminate service for Shale simulation
    !! @param mpiRank MPI Rank of requesting process
    !! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	interface
		subroutine lbmToOneDMD_stop_service_f(mpiRank, tag, dbHandle) bind(c, name="lbmToOneDMD_stop_service")
			use iso_c_binding
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr) :: dbHandle
		end subroutine lbmToOneDMD_stop_service_f
	end interface

    !> Fortran interface to bgk_stop_service()
    !! This is a Fortran function that is used to terminate service for BGK simulation
    !! @param mpiRank MPI Rank of requesting process
    !! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	interface
		subroutine bgk_stop_service_f(mpiRank, tag, dbHandle) bind(c, name="bgk_stop_service")
			use iso_c_binding
			integer(c_int), value :: mpiRank
			character(kind=c_char) :: tag(*)
			type(c_ptr), value :: dbHandle
		end subroutine bgk_stop_service_f
	end interface

    !> Fortran interface to resFreeWrapper() TODO
	!! @param buffer
	interface 
		subroutine resFreeWrapper_internal_f(buffer) bind(c, name="resFreeWrapper")
			use iso_c_binding
			type(c_ptr), value :: buffer
		end subroutine resFreeWrapper_internal_f
	end interface

    !> Fortran interface to closeDB()
    !! This is a Fortran function that is used to close the connection to the SQLite database
	!! @param dbHandle Database to write to
	interface
		subroutine closeDB_f(dbHandle) bind(c, name="closeDB")
			use iso_c_binding
			type(c_ptr), value :: dbHandle
		end subroutine closeDB_f
	end interface

	contains

	!> Fortran interface to bgk_req_batch()
	!! @param input Array of request of length numInputs
	!! @param numInputs Length of input array
	!! @param mpiRank MPI Rank of requesting process
	!! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
	!! @return res Array of results of length numInputs
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

	!> Fortran subroutine interface to bgk_req_batch()
	!! @param input Array of request of length numInputs
	!! @param output Array of results of length numInputs
	!! @param numInputs Length of input array
	!! @param mpiRank MPI Rank of requesting process
	!! @param tag Tag corresponding to set of requests
	!! @param dbHandle Database to write to
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

	!> Fortran wrapper to free memory allocated on C side
	!! @param ptr to memory originally allocated on C side
	subroutine bgk_resFreeWrapper_f(ptr)
		use iso_c_binding
		type(bgk_result_f), pointer :: ptr(:)
		type(c_ptr) :: intermediate

		intermediate = c_loc(ptr)
		call resFreeWrapper_internal_f(intermediate)
	end subroutine bgk_resFreeWrapper_f

end module alinterface_f