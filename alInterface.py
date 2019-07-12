from enum import Enum
import sys
import sqlite3

defaultFName = "testDB.db"
defaultTag = "DUMMY_TAG_42"

class FineGrainProvider(Enum):
    LAMMPS = 0
    MYSTIC = 1
    ACTIVELEARNER=2
    FAKE = 3

# TODO: Probably make mode an enum
def pollAndProcessFGSRequests(rankArr, mode, dbPath, tag):
    reqNumArr = [0] * len(rankArr)

    # TODO: Figure out a way to stop that isn't ```kill - 9```
    while True:
        for i in range(0, len(rankArr)):
            rank = rankArr[i]
            req = reqNumArr[i]
            sqlDB = sqlite3.connect(dbPath)
            sqlCursor = sqlDB.cursor()
            selString = "SELECT * FROM REQS WHERE RANK=? AND REQ=? AND TAG=?;"
            selArgs = (rank, req, tag)
            for row in sqlCursor.execute(selString, selArgs):
                #Process row to arguments
                temperature = row[3]
                density = [row[4], row[5], row[6], row[7]]
                charges = [row[8], row[9], row[10], row[11]]
                #Get results
                viscosity = 0.0
                thermalConductivity = 0.0
                diffCoeff = [0.0] * 10
                if mode == FineGrainProvider.LAMMPS:
                    # call lammps with args
                    # TODO
                    pass
                elif mode == FineGrainProvider.MYSTIC:
                    # call mystic: I think Mystic will handle most of our logic?
                    # TODO
                    pass
                elif mode == FineGrainProvider.ACTIVELEARNER:
                    # This is probably more for the Nick stuff
                    #  Ask Learner
                    #     We good? Return value
                    #  Check LUT
                    #     We good? Return value
                    #  Call LAMMPS
                    #     Go get a coffee, then return value. And add to LUT (?)
                    # TODO
                    pass
                elif mode == FineGrainProvider.FAKE:
                    # Simplest stencil imaginable
                    diffCoeff[7] = (temperature + density[0] + charges[3]) / 3
                # Write the result
                insString = "INSERT INTO RESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                insArgs = (tag, rank, req, viscosity, thermalConductivity) + tuple(diffCoeff)
                sqlCursor.execute(insString, insArgs)
                sqlDB.commit()
                # Increment the request number
                reqNumArr[i] = reqNumArr[i] + 1
            sqlCursor.close()
            sqlDB.close()
        #Probably some form of delay?
    


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
    pollAndProcessFGSRequests([0], FineGrainProvider.FAKE, fName, tag)