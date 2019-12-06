import argparse
from alInterface import BGKOutputs, insertResult, ResultProvenance, ALInterfaceMode, getGroundishTruthVersion, SolverCode
import numpy as np
import sqlite3

def procFileAndInsert(tag, dbPath, rank, reqid, lammpsMode, solverCode):
    if solverCode == SolverCode.BGK:
        # Open file
        # Need to remove leading I
        resAdd = np.loadtxt("mutual_diffusion.csv", converters = {0: lambda s: -0.0})
        # Write results to an output namedtuple
        bgkOutput = BGKOutputs(Viscosity=0.0, ThermalConductivity=0.0, DiffCoeff=[0.0]*10)
        bgkOutput.DiffCoeff[0] = resAdd[6]
        bgkOutput.DiffCoeff[1] = resAdd[7]
        bgkOutput.DiffCoeff[2] = resAdd[8]
        # Write the tuple
        if(lammpsMode == ALInterfaceMode.LAMMPS):
            insertResult(rank, tag, dbPath, reqid, bgkOutput, ResultProvenance.LAMMPS)
        elif(lammpsMode == ALInterfaceMode.FASTLAMMPS):
            insertResult(rank, tag, dbPath, reqid, bgkOutput, ResultProvenance.FASTLAMMPS)
        else:
            raise Exception('Using Unsupported LAMMPS Mode')
        outputList = []
        outputList.append(bgkOutput.Viscosity)
        outputList.append(bgkOutput.ThermalConductivity)
        outputList.extend(bgkOutput.DiffCoeff)
        outputList.append(getGroundishTruthVersion(SolverCode.BGK))
        return np.asarray(outputList)
    elif solverCode == SolverCode.BGKMASSES:
        # Open file
        # Need to remove leading I
        resAdd = np.loadtxt("mutual_diffusion.csv", converters = {0: lambda s: -0.0})
        # Write results to an output namedtuple
        bgkOutput = BGKMassesOutputs(Viscosity=0.0, ThermalConductivity=0.0, DiffCoeff=[0.0]*10)
        bgkOutput.DiffCoeff[0] = resAdd[6]
        bgkOutput.DiffCoeff[1] = resAdd[7]
        bgkOutput.DiffCoeff[2] = resAdd[8]
        # Write the tuple
        if(lammpsMode == ALInterfaceMode.LAMMPS):
            insertResult(rank, tag, dbPath, reqid, bgkOutput, ResultProvenance.LAMMPS)
        elif(lammpsMode == ALInterfaceMode.FASTLAMMPS):
            insertResult(rank, tag, dbPath, reqid, bgkOutput, ResultProvenance.FASTLAMMPS)
        else:
            raise Exception('Using Unsupported LAMMPS Mode')
        outputList = []
        outputList.append(bgkOutput.Viscosity)
        outputList.append(bgkOutput.ThermalConductivity)
        outputList.extend(bgkOutput.DiffCoeff)
        outputList.append(getGroundishTruthVersion(SolverCode.BGKMASSES))
        return np.asarray(outputList)
    elif solverCode == SolverCode.BGKARBIT:
        # Will need to rewrite this to account for matching species
        raise Exception('Not Implemented')

def insertGroundishTruth(dbPath, outLammps, solverCode):
    if solverCode == SolverCode.BGK:
        #Pull data to write
        inLammps = np.loadtxt("inputs.txt")
        #np.savetxt("outputs.txt", outLammps)
        #Connect to DB
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKGND VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = tuple(inLammps.tolist()) + tuple(outLammps.tolist())
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    elif solverCode == SolverCode.BGKMASSES:
        #Pull data to write
        inLammps = np.loadtxt("inputs.txt")
        #np.savetxt("outputs.txt", outLammps)
        #Connect to DB
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKMASSESGND VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = tuple(inLammps.tolist()) + tuple(outLammps.tolist())
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    elif solverCode == SolverCode.BGKARBIT:
        #Pull data to write
        inLammps = np.loadtxt("inputs.txt")
        #np.savetxt("outputs.txt", outLammps)
        #Connect to DB
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKARBITGND VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = tuple(inLammps.tolist()) + tuple(outLammps.tolist())
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultRank = 0
    defaultID = 0
    defaultProcessing = ALInterfaceMode.LAMMPS
    defaultSolver = SolverCode.BGK

    argParser = argparse.ArgumentParser(description='Python Driver to Convert LAMMPS BGK Result into DB Entry')

    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-r', '--rank', action='store', type=int, required=False, default=defaultRank, help="MPI Rank of Requester")
    argParser.add_argument('-i', '--id', action='store', type=int, required=False, default=defaultID, help="Request ID")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-m', '--mode', action='store', type=int, required=False, default=defaultProcessing, help="Default Request Type (LAMMPS=0)")
    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")

    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    rank = args['rank']
    reqid = args['id']
    mode = ALInterfaceMode(args['mode'])
    code = SolverCode(args['code'])

    resultArr = procFileAndInsert(tag, fName, rank, reqid, mode, code)
    if(mode == ResultProvenance.LAMMPS):
        insertGroundishTruth(fName, resultArr, code)
