CC=gcc
CXX=g++
MPICC=mpicc
MPICXX=mpic++
FC=gfortran
AR=ar
PYTHON=python

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib

AR_FLAGS=-rcs
CXXFLAGS=-std=c++14
CFLAGS =
FFLAGS=
LDFLAGS=libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3

FORTLDFLAGS=

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

test: sniffTest_mpi sniffTest_serial alTester_serial sniffTest_fortranBGK

libalGlue.a: alInterface.o alInterface_f.o alGlueTypes_f.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o alInterface_f.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} ${CXXFLAGS} -I${SQLITE_INCLUDE} -c alInterface.cpp

alGlueTypes_f.o: alGlueTypes_f.f90
	${FC} ${FFLAGS} -c alGlueTypes_f.f90

alInterface_f.o: alInterface_f.f90 alGlueTypes_f.o
	${FC} ${FFLAGS} -c alInterface_f.f90

sniffTest_serial.o: sniffTest_serial.c
	${CC} ${CFLAGS} -c sniffTest_serial.c

sniffTest_serial: libalGlue.a sniffTest_serial.o
	${CXX} ${CXXFLAGS} sniffTest_serial.o ${LDFLAGS} -o sniffTest_serial

sniffTest_mpi.o: sniffTest_mpi.c
	${MPICC} ${CFLAGS} -c sniffTest_mpi.c

sniffTest_mpi: libalGlue.a sniffTest_mpi.o
	${MPICXX} sniffTest_mpi.o ${LDFLAGS} -o  sniffTest_mpi

sniffTest_fortranBGK_f.o: sniffTest_fortranBGK_f.f90 alInterface_f.o
	${FC} ${FFLAGS} -c sniffTest_fortranBGK_f.f90

sniffTest_fortranBGK_c.o: sniffTest_fortranBGK_c.cpp
	${CXX} ${CXXFLAGS} -c sniffTest_fortranBGK_c.cpp

sniffTest_fortranBGK: libalGlue.a sniffTest_fortranBGK_f.o sniffTest_fortranBGK_c.o
	${CXX} sniffTest_fortranBGK_f.o sniffTest_fortranBGK_c.o ${LDFLAGS} ${FORTLDFLAGS} -o sniffTest_fortranBGK

alTester.o: alTester.cpp
	${CXX} -c alTester.cpp

alTester_serial: libalGlue.a alTester.o
	${CXX} alTester.o ${LDFLAGS} -o alTester_serial

clean:
	rm -f ./*.o ./*.a ./*.mod ./sniffTest_serial ./sniffTest_mpi ./alTester_serial
