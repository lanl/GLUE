# All builds requre MPI
find_package(MPI REQUIRED)

# Add source files for library
add_library(GLUECode
	alInterface.cpp
	alGlueTypes_f.f90
	alInterface_f.f90
)

#Headers and Fortran Modules
target_include_directories( GLUECode PUBLIC 
	$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
	$<BUILD_INTERFACE:${CMAKE_CURRENT_BINARY_DIR}>
	$<INSTALL_INTERFACE:include>
)
set_target_properties(GLUECode PROPERTIES PUBLIC_HEADER
"${CMAKE_CURRENT_SOURCE_DIR}/include/alInterface.h;${CMAKE_CURRENT_BINARY_DIR}/alinterface_f.mod"
)

# Add TPLs to library
target_link_libraries(GLUECode PUBLIC MPI::MPI_CXX MPI::MPI_C MPI::MPI_Fortran)

# And add appropriate DB
if(SOLVER_SIDE_DB STREQUAL "SQLITE")
	find_package(SQLite3 REQUIRED)
	target_link_libraries(GLUECode PUBLIC SQLite::SQLite3)
	target_compile_definitions(GLUECode PUBLIC "SOLVER_SIDE_SQLITE")
endif()
