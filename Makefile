CC=gcc
CXX=g++
FC=gfortran
AR=ar
PYTHON=python
BASH=bash

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib

AR_FLAGS=-rcs
CXXFLAGS=-std=c++14


all: glueCode_sniffTest libalGlue.a

libalGlue.a: alInterface.o alInterface_f.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o alInterface_f.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} ${CXXFLAGS} -I${SQLITE_INCLUDE} -c alInterface.cpp 

alInterface_f.o: alInterface_f.f90
	${FC} -c alInterface_f.f90

glueCode_sniffTest.o: glueCode_sniffTest.c
	${CC} -c glueCode_sniffTest.c

glueCode_sniffTest: libalGlue.a glueCode_sniffTest.o
	${CXX}  glueCode_sniffTest.o libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3 -o glueCode_sniffTest

test: glueCode_sniffTest
	${BASH} ./glueCode_sniffTest.sh

clean:
	rm -f ./*.o ./*.a ./*.mod ./glueCode_sniffTest
