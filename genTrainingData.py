import numpy as np
import argparse
import os
from alInterface import SolverCode, BGKInputs, BGKMassesInputs, ALInterfaceMode, getAllGNDData, queueFGSJob
import getpass
import json

def genTrainingData(configStruct, uname, maxJobs):
    code = configStruct['solverCode']
    reqid = 0
    pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
    trainingDir = os.path.join(pythonScriptDir, "training")

    if code == SolverCode.BGK:
        csv = os.path.join(trainingDir, "bgk.csv")
        trainingEntries = np.loadtxt(csv)
        for row in trainingEntries:
            inArgs = BGKInputs(Temperature=row[0], Density=[row[1], row[2], 0.0, 0.0], Charges=[row[3], row[4], 0.0, 0.0])
            queueFGSJob(configStruct, uname, maxJobs, reqid, inArgs, 0, ALInterfaceMode.LAMMPS)
            reqid += 1
    elif code == SolverCode.BGKMASSES:
        csv = os.path.join(trainingDir, "bgk_masses.csv")
        trainingEntries = np.loadtxt(csv)
        for row in trainingEntries:
            inArgs = BGKMassesInputs(Temperature=row[0], Density=[row[1], row[2], 0.0, 0.0], Charges=[row[3], row[4], 0.0, 0.0], Masses=[row[5], row[6], 0.0, 0.0])
            queueFGSJob(configStruct, uname, maxJobs, reqid, inArgs, 0, ALInterfaceMode.LAMMPS)
            reqid += 1
    else:
        raise Exception('Using Unsupported Solver Code')

def printResults(gndTable, code):
    if code == SolverCode.BGK:
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
    else:
        raise Exception('Using Unsupported Solver Code')

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultSolver = SolverCode.BGK
    defaultUname = getpass.getuser()
    defaultLammps = "./lmp"
    defaultMaxJobs = 4
    defaultGenOrRead = 0
    defaultJsonFile = ""

    argParser = argparse.ArgumentParser(description='Python Driver to Convert FGS BGK Result into DB Entry')

    argParser.add_argument('-i', '--inputfile', action='store', type=str, required=False, default=defaultJsonFile, help="(JSON) Input File")
    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0, BGKMASSES=2)")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")
    argParser.add_argument('-g', '--genorread', action='store', type=int, required=False, default=defaultGenOrRead, help="Generate or Read Training Data")

    args = vars(argParser.parse_args())

    jsonFile = args['inputfile']
    configStruct = {}
    if jsonFile != "":
        with open(jsonFile) as j:
            configStruct = json.load(j)
    code = SolverCode(args['code'])
    if not 'solverCode' in configStruct:
        configStruct['solverCode'] = code
    else:
        configStruct['solverCode'] = SolverCode(configStruct['solverCode'])
    fName = args['db']
    if not 'dbFileName' in configStruct:
        configStruct['dbFileName'] = fName
    lammps = args['lammps']
    if not 'LAMMPSPath' in configStruct:
        configStruct['LAMMPSPath'] = lammps
    uname = args['uname']
    jobs = args['maxjobs']
    genOrRead = args['genorread']
    if not 'GenerateTrainingData' in configStruct:
        if(genOrRead == 0):
            configStruct['GenerateTrainingData'] = True
    if not 'ReadTrainingData' in configStruct:
        if(genOrRead == 1):
            configStruct['ReadTrainingData'] = True
    if not 'tag' in configStruct:
        configStruct['tag'] = "TESTING"

    if configStruct['GenerateTrainingData']:
        genTrainingData(configStruct, uname, jobs)
    if configStruct['ReadTrainingData']:
        results = getAllGNDData(fName, code)
        printResults(results, code)
