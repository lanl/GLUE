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
LDFLAGS=libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3

ifdef DB_EXISTENCE_SPIN
	CXXFLAGS += -DDB_EXISTENCE_SPIN
	LDFLAGS += -lstdc++fs
endif

all: libalGlue.a

test: sniffTest_mpi sniffTest_serial alTester_serial

libalGlue.a: alInterface.o alInterface_f.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o alInterface_f.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} ${CXXFLAGS} -I${SQLITE_INCLUDE} -c alInterface.cpp 

alInterface_f.o: alInterface_f.f90
	${FC} -c alInterface_f.f90

sniffTest_serial.o: sniffTest_serial.c
	${CC} -c sniffTest_serial.c

sniffTest_serial: libalGlue.a sniffTest_serial.o
	${CXX}  sniffTest_serial.o ${LDFLAGS} -o sniffTest_serial

sniffTest_mpi.o: sniffTest_mpi.c
	${MPICC} -c sniffTest_mpi.c

sniffTest_mpi: libalGlue.a sniffTest_mpi.o
	${MPICXX} sniffTest_mpi.o ${LDFLAGS} -o  sniffTest_mpi

alTester.o: alTester.cpp
	${CXX} -c alTester.cpp

alTester_serial: libalGlue.a alTester.o
	${CXX} alTester.o ${LDFLAGS} -o alTester_serial

clean:
	rm -f ./*.o ./*.a ./*.mod ./sniffTest_serial ./sniffTest_mpi ./alTester_serial
