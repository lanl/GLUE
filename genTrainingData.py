import numpy as np
import argparse
import os
from alInterface import SolverCode, BGKInputs, ALInterfaceMode, getAllGNDData, queueLammpsJob

def genTrainingData(dbPath, uname, lammps, maxJobs):
    reqid = 0

    pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
    csv = os.path.join(pythonScriptDir, "training")
    csv = os.path.join(csv, "bgk.csv")
    trainingEntries = np.loadtxt(csv)

    for row in trainingEntries:
        inArgs = BGKInputs(Temperature=row[0], Density=[row[1], row[2], 0.0, 0.0], Charges=[row[3], row[4], 0.0, 0.0])
        queueLammpsJob(uname, maxJobs, reqid, inArgs, 0, "TRAINING", dbPath, lammps, ALInterfaceMode.LAMMPS)
        reqid += 1

def printResults(gndTable):
    header = "#"
    header += "InTemperature "
    for i in range(4):
        header += "InDensity[" + str(i) + "] "
    for i in range(4):
        header += "InCharges[" + str(i) + "] "
    header += "InVersion "
    header += "OutViscosity "
    header += "OutThermalConductivity "
    for i in range(10):
        header += "OutDiffusionCoefficient[" + str(i) + "] "
    header += "OutVersion "
    print(header)

    print(gndTable)

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultSolver = SolverCode.BGK
    defaultUname = "tcg"
    defaultLammps = "./lmp"
    defaultMaxJobs = 4
    defaultGenOrRead = 0

    argParser = argparse.ArgumentParser(description='Python Driver to Convert LAMMPS BGK Result into DB Entry')

    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")
    argParser.add_argument('-g', '--genorread', action='store', type=int, required=False, default=defaultGenOrRead, help="Generate or Read Training Data")

    args = vars(argParser.parse_args())

    code = SolverCode(args['code'])
    fName = args['db']
    lammps = args['lammps']
    uname = args['uname']
    jobs = args['maxjobs']
    genOrRead = args['genorread']

    if genOrRead == 0:
        genTrainingData(fName, uname, lammps, jobs)
    else:
        results = getAllGNDData(fName, code)
        printResults(results)