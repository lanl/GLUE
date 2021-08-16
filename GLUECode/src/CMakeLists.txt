# All builds requre MPI
find_package(MPI REQUIRED)

# Add source files for library
#TODO: Refactor file structure
add_library(GLUECode
	alInterface.cpp
	alGlueTypes_f.f90
	alInterface_f.f90
)

target_include_directories(GLUECode PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Add TPLs to library
target_link_libraries(GLUECode PUBLIC MPI::MPI_CXX MPI::MPI_C MPI::MPI_Fortran)

# And add appropriate DB
if(SOLVER_SIDE_DB STREQUAL "SQLITE")
	find_package(SQLite3 REQUIRED)
	target_link_libraries(GLUECode PUBLIC SQLite::SQLite3)
	target_compile_definitions(GLUECode PUBLIC "SOLVER_SIDE_SQLITE")
endif()
