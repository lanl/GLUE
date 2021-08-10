cmake_minimum_required(VERSION 3.12)

project(GLUECode LANGUAGES CXX C Fortran)

# Require C++14
set(CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 14)

# Add option for DB Backend
set(SOLVER_SIDE_DB "SQLITE" CACHE STRING "Solver Side Database Backend (SQLITE, MYSQL)")

# All builds requre MPI
find_package(MPI REQUIRED)

# Add source files for library
#TODO: Refactor file structure
add_library(GLUECode
	alInterface.cpp
	alGlueTypes_f.f90
	alInterface_f.f90
)

# Add TPLs to library
target_link_libraries(GLUECode PUBLIC MPI::MPI_CXX MPI::MPI_C MPI::MPI_Fortran)

# And add appropriate DB

if(SOLVER_SIDE_DB EQUAL "SQLITE")
	find_package(SQLite3 REQUIRED)
	target_link_libraries(GLUECode PUBLIC SQLite::SQLite3)
endif()

