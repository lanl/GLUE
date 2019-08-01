from enum import Enum
import sqlite3
import argparse
import slurmInterface

defaultFName = "testDB.db"
defaultTag = "DUMMY_TAG_42"
defaultLammps = "./lmp"

class FineGrainProvider(Enum):
    LAMMPS = 0
    MYSTIC = 1
    ACTIVELEARNER=2
    FAKE = 3

def pollAndProcessFGSRequests(rankArr, mode, dbPath, tag, lammps):
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
            reqQueue = []
            # Get current set of requests
            for row in sqlCursor.execute(selString, selArgs):
                #Process row to arguments
                temperature = row[3]
                density = [row[4], row[5], row[6], row[7]]
                charges = [row[8], row[9], row[10], row[11]]
                #Enqueue task
                reqQueue.append((req, temperature, density, charges))
                #Increment reqNum
                reqNumArr[i] = reqNumArr[i] + 1
            sqlCursor.close()
            sqlDB.close()
            # Process tasks based on mode
            for task in reqQueue:
                if mode == FineGrainProvider.LAMMPS:
                    # call lammps with args as slurmjob
                    # slurmjob will write result back
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
                    viscosity = 0.0
                    thermalConductivity = 0.0
                    diffCoeff = [0.0] * 10
                    diffCoeff[7] = (task[1] + task[2][0] + task[3][3]) / 3
                    # Write the result
                    sqlDB = sqlite3.connect(dbPath)
                    sqlCursor = sqlDB.cursor()
                    insString = "INSERT INTO RESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    insArgs = (tag, rank, task[0], viscosity, thermalConductivity) + tuple(diffCoeff)
                    sqlCursor.execute(insString, insArgs)
                    sqlDB.commit()
                    sqlCursor.close()
                    sqlDB.close()
        #Probably some form of delay?


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description='Python Shim for LAMMPS and AL')

    argParser.add_argument('--tag', action='store', type=str, required=False, default=defaultTag)
    argParser.add_argument('--lammps', action='store', type=str, required=False, default=defaultLammps)
    argParser.add_argument('--db', action='store', type=str, required=False, default=defaultFName)

    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    lammps = args['lammps']

    pollAndProcessFGSRequests([0], FineGrainProvider.FAKE, fName, tag, lammps)
