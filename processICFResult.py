import argparse
from alInterface import ICFOutputs, insertLammpsResult
import numpy as np

def procFileAndInsert(tag, dbPath, rank, reqid, inFile):
    # Open file
    # Need to remove leading I
    resAdd = np.loadtxt(inFile, converters = {0: lambda s: -0.0})
    # Write results to an output namedtuple
    icfOutput = ICFOutputs(Viscosity=0.0, ThermalConductivity=0.0, DiffCoeff=[0.0]*10)
    icfOutput.DiffCoeff[0] = resAdd[6]
    icfOutput.DiffCoeff[1] = resAdd[7]
    icfOutput.DiffCoeff[2] = resAdd[8]
    # Write the tuple
    insertLammpsResult(rank, tag, dbPath, reqid, icfOutput)


if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultRank = 0
    defaultID = 0
    defaultCSV = "./mutual_diffusion.csv"

    argParser = argparse.ArgumentParser(description='Python Driver to Convert LAMMPS ICF Result into DB Entry')

    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-r', '--rank', action='store', type=int, required=False, default=defaultRank, help="MPI Rank of Requester")
    argParser.add_argument('-i', '--id', action='store', type=int, required=False, default=defaultID, help="Request ID")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-f', '--file', action='store', type=str, required=False, default=defaultCSV, help="Filename to process")

    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    rank = args['rank']
    reqid = args['id']
    inFile = args['file']

    procFileAndInsert(tag, fName, rank, reqid, inFile)