import argparse
from alInterface import BGKOutputs, insertResult, ResultProvenance, ALInterfaceMode, getGroundishTruthVersion, SolverCode
from writeLammpsScript import write_output_coeff
import numpy as np
import sqlite3
import os
import re

def speciesNotationToArrayIndex(in0, in1):
    (spec0, spec1) = sorted( (in0, in1) )
    if (spec0, spec1) == (0, 0):
        return 0
    elif (spec0, spec1) == (0, 1):
        return 1
    elif (spec0, spec1) == (0, 2):
        return 2
    elif (spec0, spec1) == (0, 3):
        return 3
    elif (spec0, spec1) == (1, 1):
        return 4
    elif (spec0, spec1) == (1, 2):
        return 5
    elif (spec0, spec1) == (1, 3):
        return 6
    elif (spec0, spec1) == (2, 2):
        return 7
    elif (spec0, spec1) == (2, 3):
        return 8
    elif (spec0, spec1) == (3, 3):
        return 9
    else:
        raise Exception('Improper Species Indices:' + str(spec0) + ',' + str(spec1))

def procBGKCSVFile(char, fname):
    retVal = -0.0
    stripString = char + '='
    with open(fname) as f:
        for line in f:
            stripString = line.strip(stripString)
            retVal = float(stripString)
    return retVal

def matchLammpsOutputsToArgs(outputDirectory):
    # Special thanks to Scot Halverson for figuring out clean solution
    diffCoeffs = 10*[0.0]
    visco = -0.0
    thermoCond = 0.0
    # Iterate over all output files
    for dirFile in os.listdir(outputDirectory):
        # Is this a diffusion output file?
        if re.match("diffusion_coefficient_\d+.csv", dirFile):
            # Pull the diffusion value out first
            diffVal = procBGKCSVFile('D', os.path.join(outputDirectory, dirFile))
            indexString = dirFile.replace("diffusion_coefficient_", "")
            indexString = indexString.replace(".csv", "")
            if len(indexString) != 2:
                raise Exception(dirFile + " is not mappable to a species index")
            # Map species indices to BGK indices
            outIndex = speciesNotationToArrayIndex( int(indexString[0]), int(indexString[1]) )
            # And write the result to the output array
            diffCoeffs[outIndex] = diffVal
        # Or is it a viscosity file?
        if re.match("viscosity_coefficient.csv", dirFile):
            visco = procBGKCSVFile('v', os.path.join(outputDirectory, dirFile))
        # Or a thermal conductivity file
        if re.match("conductivity_coefficient.csv", dirFile):
            thermoCond = procBGKCSVFile('k', os.path.join(outputDirectory, dirFile))
    return (diffCoeffs, visco, thermoCond)

def procOutputsAndProcess(tag, dbPath, rank, reqid, lammpsMode, solverCode):
    if solverCode == SolverCode.BGK:
        # Pull densities
        densities = np.loadtxt("densities.txt")
        # Pull zeroes indices
        zeroDensitiesIndex = np.loadtxt("zeroes.txt").astype(int)
        # Generate coefficient files
        write_output_coeff(densities, zeroDensitiesIndex)
        # Get outputs array(s)
        (diffCoeffs, viscosity, thermalConductivity) = matchLammpsOutputsToArgs(os.getcwd())
        # Write results to an output namedtuple
        bgkOutput = BGKOutputs(Viscosity=viscosity, ThermalConductivity=thermalConductivity, DiffCoeff=diffCoeffs)
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
    else:
        # Unknown solver code
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

    resultArr = procOutputsAndProcess(tag, fName, rank, reqid, mode, code)
    if(mode == ResultProvenance.LAMMPS):
        insertGroundishTruth(fName, resultArr, code)
