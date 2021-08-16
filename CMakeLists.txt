cmake_minimum_required(VERSION 3.14)

project(GLUECode LANGUAGES CXX C Fortran)

# Require C++14
set(CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 14)

# Add option for DB Backend
set(SOLVER_SIDE_DB "SQLITE" CACHE STRING "Set Database Backend For C Side Of Code")
set_property(CACHE SOLVER_SIDE_DB PROPERTY STRINGS "SQLITE" "MYSQL")


# All builds requre MPI
find_package(MPI REQUIRED)

# Add source files for library
#TODO: Refactor file structure
add_library(GLUECode
	alInterface.cpp
	alDBInterfaces.cpp
	alGlueTypes_f.f90
	alInterface_f.f90
)

# Add TPLs to library
target_link_libraries(GLUECode PUBLIC MPI::MPI_CXX MPI::MPI_C MPI::MPI_Fortran)

# And add appropriate DB
if(SOLVER_SIDE_DB STREQUAL "SQLITE")
	find_package(SQLite3 REQUIRED)
	target_link_libraries(GLUECode PUBLIC SQLite::SQLite3)
	target_compile_definitions(GLUECode PUBLIC "SOLVER_SIDE_SQLITE")
endif()

# And now build the testers
add_executable(sniffTest_MPI sniffTest_mpi.c)
target_link_libraries(sniffTest_MPI PRIVATE GLUECode)