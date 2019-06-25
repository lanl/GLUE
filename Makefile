CC=gcc
CXX=g++
PYTHON=python

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib


all: test

test: individualReqs

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} -I${SQLITE_INCLUDE} -c alInterface.cpp 

individualReqs_tester.o: individualReqs_tester.c
	${CC} -c individualReqs_tester.c

individualReqs: alInterface.o individualReqs_tester.o
	${CXX}  alInterface.o individualReqs_tester.o -L${SQLITE_LIBDIR} -lsqlite3 -o individualReqs

clean:
	rm -f ./*.o ./individualReqs
