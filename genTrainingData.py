import numpy as np
import argparse
from alInterface import SolverCode, BGKInputs, ALInterfaceMode, getAllGNDData, queueLammpsJob

def genTrainingData(dbPath, uname, lammps, maxJobs):
    reqid = 0

    temperature = [10.999999]
    dens0 = [9.99999992439103e+22]
    dens1 = 9.99999998583057e+22]
    cha0 = [0.713264]
    cha1 = [2.334522]

    for t in temperature:
        for d0 in dens0:
            for d1 in dens1:
                for c0 in cha0:
                    for c1 in cha1:
                        inArgs = BGKInputs(Temperature=t, Density=[dens0, dens1, 0.0, 0.0], Charges=[cha0, cha1, 0.0, 0.0])
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

    argParser = argparse.ArgumentParser(description='Python Driver to Convert LAMMPS BGK Result into DB Entry')

    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")


    args = vars(argParser.parse_args())

    code = SolverCode(args['code'])
    fName = args['db']
    lammps = args['lammps']
    uname = args['uname']
    jobs = args['maxjobs']

    genTrainingData(dbPath, uname, lammps, maxJobs)
    results = getAllGNDData(fName, code)
    printResults(results)