CC=gcc
CXX=g++
FC=gfortran
AR=ar
PYTHON=python

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib

AR_FLAGS=-rcs


all: test libalGlue.a

test: glueCode_sniffTest

libalGlue.a: alInterface.o alInterface_f.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o alInterface_f.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} -I${SQLITE_INCLUDE} -c alInterface.cpp 

alInterface_f.o: alInterface_f.f90
	${FC} -c alInterface_f.f90

glueCode_sniffTest.o: glueCode_sniffTest.c
	${CC} -c glueCode_sniffTest.c

glueCode_sniffTest: libalGlue.a glueCode_sniffTest.o
	${CXX}  glueCode_sniffTest.o libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3 -o glueCode_sniffTest

clean:
	rm -f ./*.o ./*.a ./*.mod ./glueCode_sniffTest ./test.db
