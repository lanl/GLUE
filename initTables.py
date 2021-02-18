import sqlite3
import argparse
import os
import time
import json
from glueCodeTypes import SolverCode
from glueArgParser import processGlueCodeArguments
from glueSQLHelpers import getSQLArrGenString


def initSQLTables(configStruct):
    dbPath = configStruct['dbFileName']
    packetType = configStruct['solverCode']
    reqString = ""
    resString = ""
    resFString = ""
    gndString = ""
    if packetType == SolverCode.BGK:
        dropReqString = "DROP TABLE IF EXISTS BGKREQS;"
        dropResString = "DROP TABLE IF EXISTS BGKRESULTS;"
        dropResFString = "DROP TABLE IF EXISTS BGKFASTRESULTS;"
        reqString = "CREATE TABLE BGKREQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, TEMPERATURE REAL, "
        reqString += getSQLArrGenString("DENSITY", float, 4)
        reqString += getSQLArrGenString("CHARGES", float, 4)
        reqString +=  "REQTYPE INT);"
        resString = "CREATE TABLE BGKRESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, "
        resString += getSQLArrGenString("DIFFCOEFF", float, 10)
        resString += "PROVENANCE INT NOT NULL);"
        resFString = "CREATE TABLE BGKFASTRESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, "
        resFString += getSQLArrGenString("DIFFCOEFF", float, 10)
        resFString += "PROVENANCE INT NOT NULL);"
        gndString = "CREATE TABLE IF NOT EXISTS BGKGND(TEMPERATURE REAL, "
        gndString += getSQLArrGenString("DENSITY", float, 4)
        gndString += getSQLArrGenString("CHARGES", float, 4)
        gndString += "INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, "
        gndString += getSQLArrGenString("DIFFCOEFF", float, 10)
        gndString += "OUTVERSION REAL);"
        logString = "CREATE TABLE IF NOT EXISTS BGKALLOGS(TEMPERATURE REAL, "
        logString += getSQLArrGenString("DENSITY", float, 4)
        logString += getSQLArrGenString("CHARGES", float, 4)
        logString += "INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, "
        logString += getSQLArrGenString("DIFFCOEFF", float, 10)
        logString += "OUTVERSION REAL);"
    elif packetType == SolverCode.BGKMASSES:
        dropReqString = "DROP TABLE IF EXISTS BGKMASSESREQS;"
        dropResString = "DROP TABLE IF EXISTS BGKMASSESRESULTS;"
        reqString = "CREATE TABLE BGKMASSESREQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, MASSES_0 REAL, MASSES_1 REAL, MASSES_2 REAL, MASSES_3 REAL, REQTYPE INT);"
        resString = "CREATE TABLE BGKMASSESRESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, PROVENANCE INT NOT NULL);"
        gndString = "CREATE TABLE IF NOT EXISTS BGKMASSESGND(TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, MASSES_0 REAL, MASSES_1 REAL, MASSES_2 REAL, MASSES_3 REAL, INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, OUTVERSION REAL);"
        logString = "CREATE TABLE IF NOT EXISTS BGKALLOGSMASSESGND(TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL, MASSES_0 REAL, MASSES_1 REAL, MASSES_2 REAL, MASSES_3 REAL, INVERSION REAL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL, OUTVERSION REAL);"
    else:
        raise Exception('Using Unsupported Solver Code')

    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()

    sqlCursor.execute(dropReqString)
    sqlCursor.execute(dropResString)
    sqlCursor.execute(dropResFString)
    sqlDB.commit()

    sqlCursor.execute(reqString)
    sqlCursor.execute(resString)
    sqlCursor.execute(gndString)
    sqlCursor.execute(logString)
    sqlCursor.execute(resFString)

    sqlDB.commit()
    sqlDB.close()

    #Spin until file exists
    while not os.path.exists(dbPath):
        time.sleep(1)

if __name__ == "__main__":
    configStruct = processGlueCodeArguments()

    initSQLTables(configStruct)