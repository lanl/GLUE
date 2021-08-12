CC=gcc
CXX=g++
MPICC=mpicc
MPICXX=mpic++
MPIFC=mpifort
FC=gfortran
AR=ar
PYTHON=python

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib

AR_FLAGS=-rcs
CXXFLAGS=-std=c++14 -g
CFLAGS = -g
FFLAGS= -g
LDFLAGS=libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3 -g

FORTLDFLAGS=

# TODO: Restructure this as we now need to use MPICC
ifeq ($(CXX),g++)
	FORTLDFLAGS += -lgfortran
endif
ifeq ($(CXX),icpc)
	FORTLDFLAGS += -lifcore
endif
ifeq ($(FC),gfortran)
	ifeq ($(CXX),clang++)
		FORTLDFLAGS += -lgfortran
	endif
endif
ifeq ($(CXX),pgc++)
	FORTLDFLAGS += -pgf90libs
endif

ifdef DB_EXISTENCE_SPIN
	CXXFLAGS += -DDB_EXISTENCE_SPIN
	LDFLAGS += -lstdc++fs
endif

all: libalGlue.a

test: sniffTest_mpi sniffTest_serial alTester_serial sniffTest_fortranBGK stressTest_analyticICF stressTest_analyticICF_collective fullTest_collectiveICF

libalGlue.a: alInterface.o alInterface_f.o alGlueTypes_f.o alDBInterfaces.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o alInterface_f.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${MPICXX} ${CXXFLAGS} -I${SQLITE_INCLUDE} -c alInterface.cpp

alDBInterfaces.o: alDBInterfaces.cpp alDBInterfaces.hpp
	${MPICXX} ${CXXFLAGS} -I${SQLITE_INCLUDE} -c alDBInterfaces.cpp

alGlueTypes_f.o: alGlueTypes_f.f90
	${MPIFC} ${FFLAGS} -c alGlueTypes_f.f90

alInterface_f.o: alInterface_f.f90 alGlueTypes_f.o
	${MPIFC} ${FFLAGS} -c alInterface_f.f90

sniffTest_serial.o: sniffTest_serial.c
	${MPICC} ${CFLAGS} -c sniffTest_serial.c

sniffTest_serial: libalGlue.a sniffTest_serial.o
	${MPICXX} ${CXXFLAGS} sniffTest_serial.o ${LDFLAGS} -o sniffTest_serial

sniffTest_mpi.o: sniffTest_mpi.c
	${MPICC} ${CFLAGS} -c sniffTest_mpi.c

sniffTest_mpi: libalGlue.a sniffTest_mpi.o
	${MPICXX} sniffTest_mpi.o ${LDFLAGS} -o  sniffTest_mpi

sniffTest_fortranBGK_f.o: sniffTest_fortranBGK_f.f90 alInterface_f.o
	${MPIFC} ${FFLAGS} -c sniffTest_fortranBGK_f.f90

sniffTest_fortranBGK_c.o: sniffTest_fortranBGK_c.cpp
	${MPICXX} ${CXXFLAGS} -c sniffTest_fortranBGK_c.cpp

sniffTest_fortranBGK: libalGlue.a sniffTest_fortranBGK_f.o sniffTest_fortranBGK_c.o
	${MPICXX} sniffTest_fortranBGK_f.o sniffTest_fortranBGK_c.o ${LDFLAGS} ${FORTLDFLAGS} -o sniffTest_fortranBGK

stressTest_analyticICF: libalGlue.a stressTest_analyticICF.o
	${MPICXX} ${CXXFLAGS} stressTest_analyticICF.o ${LDFLAGS} -o stressTest_analyticICF

stressTest_analyticICF.o: stressTest_analyticICF.c
	${MPICC} ${CFLAGS} -c stressTest_analyticICF.c

stressTest_analyticICF_collective: libalGlue.a stressTest_analyticICF_collective.o
	${MPICXX} ${CXXFLAGS} stressTest_analyticICF_collective.o ${LDFLAGS} -o stressTest_analyticICF_collective

stressTest_analyticICF_collective.o: stressTest_analyticICF_collective.c
	${MPICC} ${CFLAGS} -c stressTest_analyticICF_collective.c

fullTest_collectiveICF: libalGlue.a fullTest_collectiveICF.o
	${MPICXX} ${CXXFLAGS} fullTest_collectiveICF.o ${LDFLAGS} -o fullTest_collectiveICF

fullTest_collectiveICF.o: fullTest_collectiveICF.c
	${MPICC} ${CFLAGS} -c fullTest_collectiveICF.c

alTester.o: alTester.cpp
	${MPICXX} -c alTester.cpp

alTester_serial: libalGlue.a alTester.o
	${MPICXX} alTester.o ${LDFLAGS} -o alTester_serial

clean:
	rm -f ./*.o ./*.a ./*.mod ./sniffTest_serial ./sniffTest_mpi ./alTester_serial ./stressTest_analyticICF
