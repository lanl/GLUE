import sys
import sqlite3

defaultFName = "testDB.db"
defaultTag = "DUMMY_TAG_42"

def initSQLTables(dbPath, tag):
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()

    reqString = "CREATE TABLE REQS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, TEMPERATURE REAL, DENSITY_0 REAL, DENSITY_1 REAL, DENSITY_2 REAL, DENSITY_3 REAL, CHARGES_0 REAL, CHARGES_1 REAL, CHARGES_2 REAL, CHARGES_3 REAL);"
    resString =  "CREATE TABLE RESULTS(TAG TEXT NOT NULL, RANK INT NOT NULL, REQ INT NOT NULL, VISCOSITY REAL, THERMAL_CONDUCT REAL, DIFFCOEFF_0 REAL, DIFFCOEFF_1 REAL, DIFFCOEFF_2 REAL, DIFFCOEFF_3 REAL, DIFFCOEFF_4 REAL, DIFFCOEFF_5 REAL, DIFFCOEFF_6 REAL, DIFFCOEFF_7 REAL, DIFFCOEFF_8 REAL, DIFFCOEFF_9 REAL);"

    sqlCursor.execute(reqString)
    sqlCursor.execute(resString)
    sqlDB.commit()

    sqlDB.close()

if __name__ == "__main__":
    fName = ""
    tag = ""
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = defaultTag
    if len(sys.argv) > 2:
        fName = sys.argv[2]
    else:
        fName = defaultFName
    initSQLTables(fName, tag)