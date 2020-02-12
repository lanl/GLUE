program sniff
	use alinterface_f
	use algluetypes_f
	use iso_c_binding
	implicit none

	type(bgk_request_f) :: req
	type(bgk_result_f) :: ret
	type(c_ptr) :: dbHandle
	integer(c_int) :: mpiHandle
	type(bgk_request_f) :: batchReq(12)
	type(bgk_result_f), pointer :: batchRet(:)
	integer :: i

	mpiHandle = 0

	req%temperature = 4.0
	req%density(1) = 6.0
	req%charges(4) = 5.0

	dbHandle = initDB_f(mpiHandle, "foo.db"//CHAR(0))

	ret = bgk_req_single_f(req, mpiHandle, "TAG"//CHAR(0), dbHandle)
	print *,ret%diffusionCoefficient(8)

	! Set some values to process
	do i = 1,12
		batchReq(i)%temperature = 13.4
		batchReq(i)%density(1) = i * 2.45
		batchReq(i)%charges(4) = 7.32
	end do

	! And then set a value we can check
	batchReq(7)%temperature = 5.0
	batchReq(7)%density(1) = 22.0
	batchReq(7)%charges(4) = 3.0

	batchRet = bgk_req_batch_f(batchReq, 12,  mpiHandle, "TAG"//CHAR(0), dbHandle)

	print *,batchRet(7)%diffusionCoefficient(8)

	call bgk_stop_service_f(mpiHandle, "TAG"//CHAR(0), dbHandle)
	call closeDB_f(dbHandle)

end program sniff
