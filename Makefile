CC=gcc
CXX=g++
AR=ar
PYTHON=python

SQLITE_DIR=
SQLITE_INCLUDE=${SQLITE_DIR}/include
SQLITE_LIBDIR=${SQLITE_DIR}/lib

AR_FLAGS=-rcs


all: test libalGlue.a

test: individualReqs batchReqs

libalGlue.a: alInterface.o
	${AR} ${AR_FLAGS} libalGlue.a alInterface.o

alInterface.o: alInterface.cpp alInterface.h alInterface.hpp
	${CXX} -I${SQLITE_INCLUDE} -c alInterface.cpp 

individualReqs_tester.o: individualReqs_tester.c
	${CC} -c individualReqs_tester.c

batchReqs_tester.o: batchReqs_tester.c
	${CC} -c batchReqs_tester.c

individualReqs: libalGlue.a individualReqs_tester.o
	${CXX}  individualReqs_tester.o libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3 -o individualReqs

batchReqs: libalGlue.a batchReqs_tester.o
	${CXX}  batchReqs_tester.o libalGlue.a -L${SQLITE_LIBDIR} -lsqlite3 -o batchReqs

clean:
	rm -f ./*.o ./individualReqs ./batchReqs
