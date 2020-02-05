from enum import Enum, IntEnum
import sqlite3
import argparse
import collections
from collections.abc import Iterable
from SM import Wigner_Seitz_radius
import os
import shutil
import numpy as np
import csv
import time
import subprocess
import getpass
from writeLammpsScript import check_zeros_trace_elements
from glueCodeTypes import ALInterfaceMode, SolverCode, ResultProvenance, LearnerBackend, BGKInputs, BGKMassesInputs, BGKOutputs, BGKMassesOutputs

def getGroundishTruthVersion(packetType):
    if packetType == SolverCode.BGK:
        return 2.1
    elif packetType == SolverCode.BGKMASSES:
        return 1.0
    else:
        raise Exception('Using Unsupported Solver Code')

def getSelString(packetType):
    if packetType == SolverCode.BGK:
        return "SELECT * FROM BGKREQS WHERE RANK=? AND REQ=? AND TAG=?;"
    else:
        raise Exception('Using Unsupported Solver Code')

def getGNDStringAndTuple(lammpsArgs):
    selString = ""
    selTup = ()
    if isinstance(lammpsArgs, BGKInputs):
        # Optimally find something bigger than machine epsilon
        epsilon = np.finfo('float64').eps
        # TODO: DRY this for later use
        selString += "SELECT * FROM BGKGND WHERE "
        #Temperature
        selString += "TEMPERATURE BETWEEN ? AND ? "
        selTup += (lammpsArgs.Temperature - epsilon, lammpsArgs.Temperature + epsilon)
        selString += " AND "
        #Density
        for i in range(0, 4):
            selString += "DENSITY_" + str(i) + " BETWEEN ? AND ? "
            selTup += (lammpsArgs.Density[i] - epsilon, lammpsArgs.Density[i] + epsilon)
            selString += " AND "
        #Charges
        for i in range(0, 4):
            selString += "CHARGES_" + str(i) + " BETWEEN ? AND ? "
            selTup += (lammpsArgs.Charges[i] - epsilon, lammpsArgs.Charges[i] + epsilon)
            selString += " AND "
        #Version
        selString += "INVERSION=?;"
        selTup += (getGroundishTruthVersion(SolverCode.BGK),)
    elif isinstance(lammpsArgs, BGKMassesInputs):
        # Optimally find something bigger than machine epsilon
        epsilon = np.finfo('float64').eps
        # TODO: DRY this for later use
        selString += "SELECT * FROM BGKMASSESGND WHERE "
        #Temperature
        selString += "TEMPERATURE BETWEEN ? AND ? "
        selTup += (lammpsArgs.Temperature - epsilon, lammpsArgs.Temperature + epsilon)
        selString += " AND "
        #Density
        for i in range(0, 4):
            selString += "DENSITY_" + str(i) + " BETWEEN ? AND ? "
            selTup += (lammpsArgs.Density[i] - epsilon, lammpsArgs.Density[i] + epsilon)
            selString += " AND "
        #Charges
        for i in range(0, 4):
            selString += "CHARGES_" + str(i) + " BETWEEN ? AND ? "
            selTup += (lammpsArgs.Charges[i] - epsilon, lammpsArgs.Charges[i] + epsilon)
            selString += " AND "
        #Masses
        for i in range(0, 4):
            selString += "MASSES_" + str(i) + " BETWEEN ? AND ? "
            selTup += (lammpsArgs.Masses[i] - epsilon, lammpsArgs.Masses[i] + epsilon)
            selString += " AND "
        #Version
        selString += "INVERSION=?;"
        selTup += (getGroundishTruthVersion(SolverCode.BGKMASSES),)
    else:
        raise Exception('Using Unsupported Solver Code')
    return (selString, selTup)

def processReqRow(sqlRow, packetType):
    if packetType == SolverCode.BGK:
        #Process row to arguments
        bgkInput = BGKInputs(Temperature=float(sqlRow[3]), Density=[], Charges=[])
        bgkInput.Density.extend([sqlRow[4], sqlRow[5], sqlRow[6], sqlRow[7]])
        bgkInput.Charges.extend([sqlRow[8], sqlRow[9], sqlRow[10], sqlRow[11]])
        reqType = ALInterfaceMode(sqlRow[12])
        return (bgkInput, reqType)
    elif packetType == SolverCode.BGKMASSES:
        bgkInput = BGKMassesInputs(Temperature=float(sqlRow[3]), Density=[], Charges=[], Masses=[])
        bgkInput.Density.extend([sqlRow[4], sqlRow[5], sqlRow[6], sqlRow[7]])
        bgkInput.Charges.extend([sqlRow[8], sqlRow[9], sqlRow[10], sqlRow[11]])
        bgkInput.Masses.extend([sqlRow[12], sqlRow[13], sqlRow[14], sqlRow[15]])
        reqType = ALInterfaceMode(sqlRow[16])
        return (bgkInput, reqType)
    else:
        raise Exception('Using Unsupported Solver Code')

def writeLammpsInputs(lammpsArgs, dirPath, lammpsMode):
    # TODO: Refactor constants and general cleanup
    if isinstance(lammpsArgs, BGKInputs):
        m=np.array([3.3210778e-24,6.633365399999999e-23])
        Teq = 0
        Trun = 0
        cutoff = 0.0
        box = 0
        eps_traces = 1.e-3
        if(lammpsMode == ALInterfaceMode.LAMMPS):
            # real values of the MD simulations (long MD)
            Teq=20000
            Trun=1000000
            cutoff = 2.5
            box=40.
            p_int=10000
            s_int=5
            d_int=s_int*p_int
            eps_traces =1.e-3
        elif(lammpsMode == ALInterfaceMode.FASTLAMMPS):
            # Values for infrastructure test
            Teq=10
            Trun=10
            cutoff = 1.0
            box=20
            p_int=2
            s_int=1
            d_int=s_int*p_int
        else:
            raise Exception('Using Unsupported LAMMPS Mode')
        interparticle_radius = []
        lammpsDens = np.array(lammpsArgs.Density) 
        lammpsTemperature = lammpsArgs.Temperature
        lammpsIonization = np.array(lammpsArgs.Charges)
        lammpsMasses = m
        # Finds zeros and trace elements in the densities, then builds LAMMPS scripts.
        (species_with_zeros_LammpsDens_index, lammpsScripts)=check_zeros_trace_elements(lammpsTemperature,lammpsDens,lammpsIonization,lammpsMasses,box,cutoff,Teq,Trun,s_int,p_int,d_int,eps_traces, dirPath)
        # And now write the densities and zeroes information to files
        densFileName = os.path.join(dirPath, "densities.txt")
        np.savetxt(densFileName, lammpsDens)
        zeroesFileName = os.path.join(dirPath, "zeroes.txt")
        np.savetxt(zeroesFileName, np.asarray(species_with_zeros_LammpsDens_index))
        # And now write the inputs to a specific file for later use
        inputList = []
        inputList.append(lammpsArgs.Temperature)
        inputList.extend(lammpsArgs.Density)
        inputList.extend(lammpsArgs.Charges)
        inputList.append(getGroundishTruthVersion(SolverCode.BGK))
        Inputs_file = os.path.join(dirPath, "inputs.txt")
        np.savetxt(Inputs_file, np.asarray(inputList))
        # And return the lammps scripts
        return lammpsScripts
    else:
        raise Exception('Using Unsupported Solver Code')

def checkSlurmQueue(uname):
    try:
        runproc = subprocess.run(
            ["squeue", "-u", uname],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if runproc.returncode == 0:
            return str(runproc.stdout,"utf-8")
        else:
            print(str(runproc.stderr,"utf-8"), file=sys.stderr)
            return ""
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        return ""

def launchSlurmJob(script):
    try:
        runproc = subprocess.run(
            ["sbatch", script],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if runproc.returncode == 0:
            return str(runproc.stdout,"utf-8")
        else:
            print(str(runproc.stderr,"utf-8"), file=sys.stderr)
            return ""
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        return ""

def getSlurmQueue(uname):
    slurmOut = checkSlurmQueue(uname)
    if slurmOut == "":
        return (sys.maxsize, [])
    strList = slurmOut.splitlines()
    if len(strList) > 1:
        return (len(strList) - 1, strList[1:])
    else:
        return (0, [])

def getAllGNDData(dbPath, solverCode):
    selString = ""
    if solverCode == SolverCode.BGK:
        selString = "SELECT * FROM BGKGND;"
    elif solverCode == SolverCode.BGKMASSES:
        selString = "SELECT * FROM BGKMASSESGND;"
    else:
        raise Exception('Using Unsupported Solver Code')
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()
    gndResults = []
    for row in sqlCursor.execute(selString):
        # Add row to numpy array
        gndResults.append(row)
    sqlCursor.close()
    sqlDB.close()
    return np.array(gndResults)

def getGNDCount(dbPath, solverCode):
    selString = ""
    if solverCode == SolverCode.BGK:
        selString = "SELECT COUNT(*)  FROM BGKGND;"
    else:
        raise Exception('Using Unsupported Solver Code')
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()
    numGND = 0
    for row in sqlCursor.execute(selString):
        # Should just be one row with one value
        numGND = row[0]
    sqlCursor.close()
    sqlDB.close()
    return numGND

def buildAndLaunchLAMMPSJob(rank, tag, dbPath, uname, lammps, reqid, lammpsArgs, lammpsMode, solverCode):
    if solverCode == SolverCode.BGK or solverCode == SolverCode.BGKMASSES:
        # Mkdir ./${TAG}_${RANK}_${REQ}
        outDir = tag + "_" + str(rank) + "_" + str(reqid)
        outPath = os.path.join(os.getcwd(), outDir)
        if(not os.path.exists(outPath)):
            os.mkdir(outPath)
            # cp ${SCRIPT_DIR}/lammpsScripts/${lammpsScript}
            # Copy scripts and configuration files
            pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
            slurmEnvPath = os.path.join(pythonScriptDir, "slurmScripts")
            # Prioritize the local jobEnv.sh over the repo jobEnv.sh
            cwdJobPath = os.path.join(os.getcwd(), "jobEnv.sh")
            jobEnvFilePath = ""
            if not os.path.exists(cwdJobPath):
                jobEnvFilePath = os.path.join(slurmEnvPath, "jobEnv.sh")
            else:
                jobEnvFilePath = cwdJobPath
            shutil.copy2(jobEnvFilePath, outPath)
            bgkResultScript = os.path.join(pythonScriptDir, "processBGKResult.py")
            # Generate input files
            lammpsScripts = writeLammpsInputs(lammpsArgs, outPath, lammpsMode)
            # Generate slurm script by writing to file
            # TODO: Identify a cleaner way to handle QOS and accounts and all the fun slurm stuff?
            # TODO: DRY this
            slurmFPath = os.path.join(outPath, tag + "_" + str(rank) + "_" + str(reqid) + ".sh")
            with open(slurmFPath, 'w') as slurmFile:
                slurmFile.write("#!/bin/bash\n")
                slurmFile.write("#SBATCH -N 3\n")
                slurmFile.write("#SBATCH -n 108\n")
                slurmFile.write("#SBATCH -o " + outDir + "-%j.out\n")
                slurmFile.write("#SBATCH -e " + outDir + "-%j.err\n")
                slurmFile.write("cd " + outPath + "\n")
                slurmFile.write("source ./jobEnv.sh\n")
                # Actually call lammps
                for lammpsScript in lammpsScripts:
                    slurmFile.write("srun -n 108 " + lammps + " < " + lammpsScript + " \n")
                # Process the result and write to DB
                slurmFile.write("python3 " + bgkResultScript + " -t " + tag + " -r " + str(rank) + " -i " + str(reqid) + " -d " + os.path.realpath(dbPath) + " -m " + str(lammpsMode.value) + " -c " + str(solverCode.value) + "\n")
            # either syscall or subprocess.run slurm with the script
            launchSlurmJob(slurmFPath)
            # Then do nothing because the script itself will write the result
    else:
        raise Exception('Using Unsupported Solver Code')

def alModelStub(inArgs):
    if isinstance(inArgs, BGKInputs):
        bgkOutput = None
        return (sys.float_info.max, bgkOutput)
    else:
        raise Exception('Using Unsupported Solver Code With Interpolation Model')

def uqCheckerStub(err):
    if err < sys.float_info.max:
        return True
    else:
        return False

def getInterpModel(packetType, alBackend, dbPath):
    if alBackend == LearnerBackend.FAKE:
        return InterpModelWrapper(alModelStub, uqCheckerStub)
    if alBackend == LearnerBackend.PYTORCH:
        import nn_learner
        return BGKPytorchInterpModel(nn_learner.retrain(dbPath))
    else:
        raise Exception('Using Unsupported Active Learning Backewnd')

def simpleALErrorChecker(inputStruct):
    retVal = True
    for i in inputStruct:
        if isinstance(i, Iterable):
            if not all(i):
                retVal = False
        else:
            if not i:
                retVal = False
    return retVal

class InterpModelWrapper:
    def __init__(self, newModel, uqChecker):
        self.model = newModel
        self.uq = uqChecker
    def __call__(self, inputStruct):
        (err, output) = self.model(inputStruct)
        isLegit = self.uq(err)
        return (isLegit, output)

class BGKPytorchInterpModel(InterpModelWrapper):
    def __init__(self, newModel):
        # TODO: Asynchrony!
        self.model = newModel
    def __call__(self, inputStruct):
        (err, output) = self.model(inputStruct)
        modErr = self.model.iserrok(err)
        isLegit = simpleALErrorChecker(modErr)
        return (isLegit, output)

def getGNDCount(dbPath, solverCode):
    selString = ""
    if solverCode == SolverCode.BGK:
        selString = "SELECT COUNT(*)  FROM BGKGND;"
    elif solverCode == SolverCode.BGKMASSES:
        selString = "SELECT COUNT(*)  FROM BGKMASSESGND;"
    else:
        raise Exception('Using Unsupported Solver Code')
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()
    numGND = 0
    for row in sqlCursor.execute(selString):
        # Should just be one row with one value
        numGND = row[0]
    sqlCursor.close()
    sqlDB.close()
    return numGND

def insertResult(rank, tag, dbPath, reqid, lammpsResult, resultProvenance):
    if isinstance(lammpsResult, BGKOutputs):
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, lammpsResult.Viscosity, lammpsResult.ThermalConductivity) + tuple(lammpsResult.DiffCoeff) + (resultProvenance,)
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    elif isinstance(lammpsResult, BGKMassesOutputs):
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKMASSESRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, lammpsResult.Viscosity, lammpsResult.ThermalConductivity) + tuple(lammpsResult.DiffCoeff) + (resultProvenance,)
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    else:
        raise Exception('Using Unsupported Solver Code')

def queueLammpsJob(uname, maxJobs, reqID, inArgs, rank, tag, dbPath, lammps, modeSwitch, packetType):
    # This is a brute force call. We only want an exact LAMMPS result
    # So first, check if we have already processed this request
    outLammps = None
    selQuery = getGNDStringAndTuple(inArgs)
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()
    for row in sqlCursor.execute(selQuery[0], selQuery[1]):
        if isinstance(inArgs, BGKInputs):
            if row[22] == getGroundishTruthVersion(SolverCode.BGK):
                outLammps = BGKOutputs(Viscosity=row[10], ThermalConductivity=row[11], DiffCoeff=row[12:22])
        elif isinstance(inArgs, BGKMassesInputs):
            if row[26] == getGroundishTruthVersion(SolverCode.BGKMASSES):
                outLammps = BGKMassesOutputs(Viscosity=row[14], ThermalConductivity=row[15], DiffCoeff=row[16:26])
    if outLammps != None:
        # We had a hit, so send that
        insertResult(rank, tag, dbPath, reqID, outLammps, ResultProvenance.DB)
    else:
        # Call lammps with args as slurmjob
        # slurmjob will write result back
        launchedJob = False
        while(launchedJob == False):
            queueState = getSlurmQueue(uname)
            if queueState[0] < maxJobs:
                print("Processing REQ=" + str(reqID))
                buildAndLaunchLAMMPSJob(rank, tag, dbPath, uname, lammps, reqID, inArgs, modeSwitch, packetType)
                launchedJob = True

def pollAndProcessFGSRequests(rankArr, defaultMode, dbPath, tag, lammps, uname, maxJobs, sbatch, packetType, alBackend):
    reqNumArr = [0] * len(rankArr)

    #Spin until file exists
    while not os.path.exists(dbPath):
        time.sleep(1)
    #Get starting GNDCount of 0
    GNDcnt = 0
    #TODO: Parameterize this
    GNDthreshold = 5
    #And start the glue loop
    keepSpinning = True
    while keepSpinning:
        # logic to not hammer DB/learner with unnecessary requests
        nuGNDcnt = getGNDCount(dbPath, packetType)
        if (nuGNDcnt - GNDcnt) > GNDthreshold:
            interpModel = getInterpModel(packetType, alBackend, dbPath)
            GNDcnt = nuGNDcnt
        for i in range(0, len(rankArr)):
            rank = rankArr[i]
            req = reqNumArr[i]
            sqlDB = sqlite3.connect(dbPath)
            # SELECT request
            sqlCursor = sqlDB.cursor()
            selString = getSelString(packetType)
            selArgs = (rank, req, tag)
            reqQueue = []
            # Get current set of requests
            for row in sqlCursor.execute(selString, selArgs):
                #Process row to arguments
                solverInput = processReqRow(row, packetType)
                #Enqueue task
                reqQueue.append((req,) + solverInput)
                #Increment reqNum
                reqNumArr[i] = reqNumArr[i] + 1
            sqlCursor.close()
            sqlDB.close()
            # Process tasks based on mode
            for task in reqQueue:
                modeSwitch = defaultMode
                if task[2] != ALInterfaceMode.DEFAULT:
                    modeSwitch = task[2]
                if modeSwitch == ALInterfaceMode.LAMMPS or modeSwitch == ALInterfaceMode.FASTLAMMPS:
                    # Submit as LAMMPS job
                    queueLammpsJob(uname, maxJobs, task[0], task[1], rank, tag, dbPath, lammps, modeSwitch, packetType)
                elif modeSwitch == ALInterfaceMode.ACTIVELEARNER:
                    # General (Active) Learner
                    #  model = getLatestModelFromLearners()
                    #  (isLegitPerUQ, outputs) = model(inputs)
                    #  if isLegitPerUQ:
                    #      return outputs
                    #  else:
                    #      outputs = fineScaleSim(inputs)
                    #      queueUpdateModel(inputs, outputs)
                    #      return outputs
                    (isLegit, output) = interpModel(task[1])
                    if isLegit:
                        insertResult(rank, tag, dbPath, task[0], output, ResultProvenance.ACTIVELEARNER)
                    else:
                        queueLammpsJob(uname, maxJobs, task[0], task[1], rank, tag, dbPath, lammps, ALInterfaceMode.LAMMPS, packetType)
                elif modeSwitch == ALInterfaceMode.FAKE:
                    if packetType == SolverCode.BGK:
                        # Simplest stencil imaginable
                        bgkInput = task[1]
                        bgkOutput = BGKOutputs(Viscosity=0.0, ThermalConductivity=0.0, DiffCoeff=[0.0]*10)
                        bgkOutput.DiffCoeff[7] = (bgkInput.Temperature + bgkInput.Density[0] +  bgkInput.Charges[3]) / 3
                        # Write the result
                        insertResult(rank, tag, dbPath, task[0], bgkOutput, ResultProvenance.FAKE)
                    else:
                        raise Exception('Using Unsupported Solver Code')
                elif modeSwitch == ALInterfaceMode.KILL:
                    keepSpinning = False

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultLammps = "./lmp"
    defaultUname = getpass.getuser()
    defaultSqlite = "sqlite3"
    defaultSbatch = "/usr/bin/sbatch"
    defaultMaxJobs = 4
    defaultProcessing = ALInterfaceMode.LAMMPS
    defaultRanks = [0]
    defaultSolver = SolverCode.BGK
    defaultALBackend = LearnerBackend.FAKE

    argParser = argparse.ArgumentParser(description='Python Shim for LAMMPS and AL')

    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-q', '--sqlite', action='store', type=str, required=False, default=defaultSqlite, help="Path to sqlite3 Binary")
    argParser.add_argument('-s', '--sbatch', action='store', type=str, required=False, default=defaultSbatch, help="Path to sbatch Binary")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")
    argParser.add_argument('-m', '--mode', action='store', type=int, required=False, default=defaultProcessing, help="Default Request Type (LAMMPS=0)")
    argParser.add_argument('-r', '--ranks', nargs='+', default=defaultRanks, type=int,  help="Rank IDs to Listen For")
    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")
    argParser.add_argument('-a', '--albackend', action='store', type=int, required=False, default=defaultALBackend, help='(Active) Learning Backend to Use')


    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    lammps = args['lammps']
    uname = args['uname']
    jobs = args['maxjobs']
    sqlite = args['sqlite']
    sbatch = args['sbatch']
    ranks = args['ranks']
    mode = ALInterfaceMode(args['mode'])
    code = SolverCode(args['code'])
    alBackend = LearnerBackend(args['albackend'])

    pollAndProcessFGSRequests(ranks, mode, fName, tag, lammps, uname, jobs, sbatch, code, alBackend)
