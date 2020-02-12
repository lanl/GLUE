program sniff
	use alinterface_f
	use iso_c_binding
	implicit none

	type(bgk_request_f) :: req
	type(bgk_result_f) :: ret
	type(c_ptr) :: dbHandle
	integer(c_int) :: mpiHandle

	mpiHandle = 0

	req%temperature = 4.0
	req%density(1) = 6.0
	req%charges(4) = 5.0

	dbHandle = initDB(mpiHandle, "foo.db"//CHAR(0))

	ret = bgk_req_single(req, 0, "TAG"//CHAR(0), dbHandle)
	print *,ret%diffusionCoefficient(8)

	call bgk_stop_service(0, "TAG"//CHAR(0), dbHandle)
	call closeDB(dbHandle)

end program sniff
