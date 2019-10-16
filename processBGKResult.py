import argparse
from alInterface import BGKOutputs, insertResult, ResultProvenance, ALInterfaceMode
import numpy as np

def procFileAndInsert(tag, dbPath, rank, reqid, inFile, lammpsMode):
    # Open file
    # Need to remove leading I
    resAdd = np.loadtxt(inFile, converters = {0: lambda s: -0.0})
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


if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultRank = 0
    defaultID = 0
    defaultCSV = "./mutual_diffusion.csv"
    defaultProcessing = ALInterfaceMode.LAMMPS

    argParser = argparse.ArgumentParser(description='Python Driver to Convert LAMMPS BGK Result into DB Entry')

    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-r', '--rank', action='store', type=int, required=False, default=defaultRank, help="MPI Rank of Requester")
    argParser.add_argument('-i', '--id', action='store', type=int, required=False, default=defaultID, help="Request ID")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-f', '--file', action='store', type=str, required=False, default=defaultCSV, help="Filename to process")
    argParser.add_argument('-m', '--mode', action='store', type=int, required=False, default=defaultProcessing, help="Default Request Type (LAMMPS=0)")

    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    rank = args['rank']
    reqid = args['id']
    inFile = args['file']
    mode = ALInterfaceMode(args['mode'])

    procFileAndInsert(tag, fName, rank, reqid, inFile, mode)