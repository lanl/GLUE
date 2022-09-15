cmake_minimum_required(VERSION 3.14)

project(GLUECode LANGUAGES CXX C Fortran)

# Require C++14
set(CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 14)

# Add option for DB Backend
set(SOLVER_SIDE_DB "SQLITE" CACHE STRING "Set Database Backend For C Side Of Code")
set_property(CACHE SOLVER_SIDE_DB PROPERTY STRINGS "SQLITE")

add_subdirectory(src)
add_subdirectory(tests)

install(TARGETS GLUECode
	EXPORT GLUECodeTargets
	LIBRARY DESTINATION lib
	ARCHIVE DESTINATION lib
	RUNTIME DESTINATION bin
	INCLUDES DESTINATION include
	PUBLIC_HEADER DESTINATION include
)
install(EXPORT GLUECodeTargets
	FILE GLUECodeTargets.cmake
	NAMESPACE GLUE::
	DESTINATION lib/cmake/GLUE
)
