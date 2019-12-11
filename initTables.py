import sqlite3
import argparse
import os
import time
from alInterface import SolverCode



def initSQLTables(dbPath, packetType):
    reqString = ""
    resString = ""
    gndString = ""
    if packetType == SolverCode.BGK:
        dropReqString = "DROP TABLE IF EXISTS BGKREQS;"
        dropResString = "DROP TABLE IF EXISTS BGKRESULTS;"
        reqString = "CREATE TABLE BGKREQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, REQTYPE INT);"
        resString = "CREATE TABLE BGKRESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, PROVENANCE INT NOT NULL);"
        gndString = "CREATE TABLE IF NOT EXISTS BGKGND(TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, OUTVERSION REAL);"
    elif packetType == SolverCode.BGKMASSES:
        dropReqString = "DROP TABLE IF EXISTS BGKMASSESREQS;"
        dropResString = "DROP TABLE IF EXISTS BGKMASSESRESULTS;"
        reqString = "CREATE TABLE BGKMASSESREQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, MASSES_0 REAL, MASSES_1 REAL, MASSES_2 REAL, MASSES_3 REAL, REQTYPE INT);"
        resString = "CREATE TABLE BGKMASSESRESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, PROVENANCE INT NOT NULL);"
        gndString = "CREATE TABLE IF NOT EXISTS BGKMASSESGND(TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, MASSES_0 REAL, MASSES_1 REAL, MASSES_2 REAL, MASSES_3 REAL, INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, OUTVERSION REAL);"
    else:
        raise Exception('Using Unsupported Solver Code')

    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()

    sqlCursor.execute(dropReqString)
    sqlCursor.execute(dropResString)
    sqlDB.commit()

    sqlCursor.execute(reqString)
    sqlCursor.execute(resString)
    sqlCursor.execute(gndString)

    sqlDB.commit()
    sqlDB.close()

    #Spin until file exists
    while not os.path.exists(dbPath):
        time.sleep(1)

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultSolver = SolverCode.BGK
    argParser = argparse.ArgumentParser(description='Python To Create DB Files for LAMMPS and AL')

    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")

    args = vars(argParser.parse_args())

    fName = args['db']
    code = SolverCode(args['code'])

    initSQLTables(fName, code)