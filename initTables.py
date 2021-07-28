import sqlite3
import os
import time
from glueCodeTypes import SolverCode
from glueArgParser import processGlueCodeArguments
from glueSQLHelpers import getSQLArrGenString
from alDBHandlers import getDBHandle


def initSQLTables(configStruct):
    dbHandles = []
    cgDBSettings = configStruct['DatabaseSettings']['CoarseGrainDB']
    cgDB = getDBHandle(cgDBSettings['DatabaseURL'], cgDBSettings['DatabaseMode'], True)
    dbHandles.append(cgDB)
    fgDBSettings = configStruct['DatabaseSettings']['FineGrainDB']
    fgDB = getDBHandle(fgDBSettings['DatabaseURL'], fgDBSettings['DatabaseMode'])
    dbHandles.append(fgDB)
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
        reqString += "REQTYPE INT);"
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
    else:
        raise Exception('Using Unsupported Solver Code')

    for db in dbHandles:
        db.openCursor()

        db.execute(dropReqString)
        db.execute(dropResString)
        db.execute(dropResFString)
        db.commit()

        db.execute(reqString)
        db.execute(resString)
        db.execute(gndString)
        db.execute(logString)
        db.execute(resFString)

        db.commit()
        db.closeCursor()
        db.closeDB()

if __name__ == "__main__":
    configStruct = processGlueCodeArguments()

    initSQLTables(configStruct)
