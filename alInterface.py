from enum import Enum, IntEnum
import sqlite3
import argparse
import collections
from collections.abc import Iterable
from SM import Wigner_Seitz_radius
import os
import stat
import shutil
import numpy as np
import csv
import time
import subprocess
import getpass
import sys
import json
from writeBGKLammpsScript import check_zeros_trace_elements
from glueCodeTypes import ALInterfaceMode, SolverCode, ResultProvenance, LearnerBackend, BGKInputs, BGKMassesInputs, BGKOutputs, BGKMassesOutputs, SchedulerInterface, ProvisioningInterface
from contextlib import redirect_stdout, redirect_stderr
from Screened_Boltzman_solution import ICFAnalytical_solution
from glueArgParser import processGlueCodeArguments

def getGroundishTruthVersion(packetType):
    if packetType == SolverCode.BGK:
        return 2.2
    elif packetType == SolverCode.BGKMASSES:
        return 1.0
    else:
        raise Exception('Using Unsupported Solver Code')

def getSelString(packetType):
    if packetType == SolverCode.BGK:
        return "SELECT * FROM BGKREQS WHERE RANK=? AND REQ=? AND TAG=?;"
    else:
        raise Exception('Using Unsupported Solver Code')

def getGNDStringAndTuple(fgsArgs, configStruct):
    selString = ""
    selTup = ()
    if isinstance(fgsArgs, BGKInputs):
        # Percent error acceptable for a match
        relError = configStruct['ICFParameters']['RelativeError']
        # TODO: DRY this for later use
        selString += "SELECT * FROM BGKGND WHERE "
        #Temperature
        #TODO: Probably verify temperature is not 0 but temperature probably won't be
        selString += "ABS(? - TEMPERATURE) / TEMPERATURE < ?"
        selTup += (fgsArgs.Temperature, relError)
        selString += " AND "
        #Density
        for i in range(0, 4):
            if(fgsArgs.Density[i] != 0.0):
                selString += "ABS(? - DENSITY_" + str(i) + ") / DENSITY_" + str(i) + " < ?"
                selTup += (fgsArgs.Density[i], relError)
                selString += " AND "
        #Charges
        for i in range(0, 4):
            if(fgsArgs.Charges[i] != 0.0):
                selString += "ABS(? - CHARGES_" + str(i) + ") / CHARGES_" + str(i) + " < ?"
                selTup += (fgsArgs.Charges[i], relError)
                selString += " AND "
        #Version
        selString += "INVERSION=?;"
        selTup += (getGroundishTruthVersion(SolverCode.BGK),)
    elif isinstance(fgsArgs, BGKMassesInputs):
        # Percent error acceptable for a match
        relError = 0.0001
        # TODO: DRY this for later use
        selString += "SELECT * FROM BGKMASSESGND WHERE "
        #Temperature
        selString += "ABS(? - TEMPERATURE) / TEMPERATURE < ?"
        selTup += (fgsArgs.Temperature, relError)
        selString += " AND "
        #Density
        for i in range(0, 4):
            selString += "ABS(? - DENSITY_" + str(i) + ") / DENSITY_" + str(i) + " < ?"
            selTup += (fgsArgs.Density[i], relError)
            selString += " AND "
        #Charges
        for i in range(0, 4):
            selString += "ABS(? - CHARGES_" + str(i) + ") / CHARGES_" + str(i) + " < ?"
            selTup += (fgsArgs.Charges[i], relError)
            selString += " AND "
        #Masses
        for i in range(0, 4):
            selString += "ABS(? - MASSES_" + str(i) + ") / MASSES_" + str(i) + " < ?"
            selTup += (fgsArgs.Masses[i], relError)
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

def writeBGKLammpsInputs(fgsArgs, dirPath, glueMode):
    # TODO: Refactor constants and general cleanup
    if isinstance(fgsArgs, BGKInputs):
        m=np.array([3.3210778e-24,6.633365399999999e-23])
        Teq = 0
        Trun = 0
        cutoff = 0.0
        box = 0
        eps_traces = 1.e-3
        if(glueMode == ALInterfaceMode.FGS):
            # real values of the MD simulations (long MD)
            Teq=20000
            Trun=1000000
            cutoff = 2.5
            box=40.
            p_int=10000
            s_int=5
            d_int=s_int*p_int
            eps_traces =1.e-3
        elif(glueMode == ALInterfaceMode.FASTFGS):
            # Values for infrastructure test
            Teq=10
            Trun=10
            cutoff = 1.0
            box=20
            p_int=2
            s_int=1
            d_int=s_int*p_int
        else:
            raise Exception('Using Unsupported FGS Mode')
        interparticle_radius = []
        lammpsDens = np.array(fgsArgs.Density) 
        lammpsTemperature = fgsArgs.Temperature
        lammpsIonization = np.array(fgsArgs.Charges)
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
        inputList.append(fgsArgs.Temperature)
        inputList.extend(fgsArgs.Density)
        inputList.extend(fgsArgs.Charges)
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

def launchJobScript(binary, script, wantReturn, extraArgs=[]):
    try:
        runproc = subprocess.run(
            [binary] + extraArgs + [script],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        if runproc.returncode == 0:
            if(wantReturn):
                return str(runproc.stdout,"utf-8")
            else:
                return ""
        else:
            print(str(runproc.stderr,"utf-8"), file=sys.stderr)
            return ""
    except FileNotFoundError as err:
        print(err, file=sys.stderr)
        return ""

def getQueueUsability(uname, configStruct):
    if configStruct['SchedulerInterface'] == SchedulerInterface.SLURM:
        queueState = getSlurmQueue(uname)
        maxJobs = configStruct['SlurmScheduler']['MaxSlurmJobs']
        if queueState[0] < maxJobs:
            return True
    elif configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        return True
    elif configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        return True
    else:
        raise Exception('Using Unsupported Scheduler Mode')

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

def jobScriptBoilerplate(jobFile, outDir, configStruct):
    if configStruct['SchedulerInterface'] == SchedulerInterface.SLURM:
        jobFile.write("#!/bin/bash\n")
        jobFile.write("#SBATCH -N " + str(configStruct['SlurmScheduler']['NodesPerSlurmJob']) + "\n")
        jobFile.write("#SBATCH -o " + outDir + "-%j.out\n")
        jobFile.write("#SBATCH -e " + outDir + "-%j.err\n")
        jobFile.write("#SBATCH -p " + str(configStruct['SlurmScheduler']['SlurmPartition']) + "\n")
        jobFile.write("export LAUNCHER_BIN=srun\n")
        jobFile.write("export JOB_DISTR_ARGS=\"-n $((`lstopo --only pu | wc -l` * ${SLURM_NNODES} / " + str(configStruct['SlurmScheduler']['ThreadsPerMPIRankForSlurm']) + "  ))\"\n")
    elif configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        jobFile.write("#!/bin/bash\n")
        jobFile.write("export LAUNCHER_BIN=mpirun\n")
        jobFile.write("export JOB_DISTR_ARGS=\"-n "+ str(configStruct['BlockingScheduler']['MPIRanksForBlockingRuns']) + "\"\n")
    elif configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        jobFile.write("#!/bin/bash\n")
        # jobFile.write("export LAUNCHER_BIN=`which mpirun`\n")
        # jobFile.write("export JOB_DISTR_ARGS=\"-np " + str(configStruct['FluxScheduler']['SlotsPerJobForFlux']) + "\"\n")
        jobFile.write("export LAUNCHER_BIN=\"flux mini run\"\n")
        jobFile.write("export JOB_DISTR_ARGS=\"" + \
            "-N " + str(configStruct['FluxScheduler']['NodesPerJobForFlux']) + \
            " -n " + str(configStruct['FluxScheduler']['SlotsPerJobForFlux']) + \
            " -c " + str(configStruct['FluxScheduler']['CoresPerSlotForFlux']) + \
            "\"\n")
    else:
        raise Exception('Using Unsupported Scheduler Mode')

def prepJobEnv(outPath, jobEnvPath, configStruct):
    outFile = os.path.join(outPath, "jobEnv.sh")
    jobEnvFilePath = ""
    if "JobEnvFile" in configStruct:
        # Check if path is absolute or relative
        structPath = configStruct["JobEnvFile"]
        if(os.path.isabs(structPath)):
            jobEnvFilePath = configStruct["JobEnvFile"]
        else:
            jobEnvFilePath = os.path.join(jobEnvPath, structPath)
    else:
        # Prioritize the local jobEnv.sh over the repo jobEnv.sh
        cwdJobPath = os.path.join(os.getcwd(), "jobEnv.sh")
        if not os.path.exists(cwdJobPath):
            jobEnvFilePath = os.path.join(jobEnvPath, "jobEnv.sh")
        else:
            jobEnvFilePath = cwdJobPath
    shutil.copy2(jobEnvFilePath, outFile)

def lammpsProvisioningBoilerplate(jobFile, configStruct):
    if configStruct['ProvisioningInterface'] == ProvisioningInterface.SPACK:
        if "SpackRoot" in configStruct['SpackVariables']:
            jobFile.write("if [ -z \"${SPACK_ROOT}\" ]; then\n")
            jobFile.write("\texport SPACK_ROOT=" + configStruct['SpackVariables']['SpackRoot'] + "\n")
            jobFile.write("fi\n")
        # Call If spack exists, use it
        # TODO: Keeping glue override flag for now but will remove later
        jobFile.write("if [ -n \"${GLUE_OVERRIDE}\" ]; then\n")
        jobFile.write("\texport LAMMPS_BIN=`which lmp`\n")
        jobFile.write("elif [ -z \"${SPACK_ROOT}\" ]; then\n")
        jobFile.write("\texport LAMMPS_BIN=" + configStruct['LAMMPSPath'] + "\n")
        jobFile.write("else\n")
        # Load lammps
        # TODO: Genralize this to support more than just MPI
        jobFile.write("\tsource $SPACK_ROOT/share/spack/setup-env.sh\n")
        jobFile.write("\tspack env create -d .\n")
        jobFile.write("\tspack env activate `pwd`\n")
        jobFile.write("\tspack install " + configStruct['SpackVariables']['SpackLAMMPS'] +  " " + configStruct['SpackVariables']['SpackCompilerAndMPI'] + "\n")
        jobFile.write("\tspack load " + configStruct['SpackVariables']['SpackLAMMPS'] +  " " + configStruct['SpackVariables']['SpackCompilerAndMPI'] + "\n")
        jobFile.write("\texport LAMMPS_BIN=`which lmp`\n")
        jobFile.write("fi\n")
    elif configStruct['ProvisioningInterface'] == ProvisioningInterface.MANUAL:
        jobFile.write("export LAMMPS_BIN=`which lmp`\n")
    else:
        raise Exception('Using Unsupported Provisioning Mode')

def launchFGSJob(jobFile, configStruct):
    if configStruct['SchedulerInterface'] == SchedulerInterface.SLURM:
        launchJobScript("sbatch", jobFile, True)
    elif configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        launchJobScript("bash", jobFile, False)
    elif configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        argList = ["mini", "batch"]
        argList += ["-n"]
        argList += [str(configStruct['FluxScheduler']['SlotsPerJobForFlux'])]
        argList += ["-c"]
        argList += [str(configStruct['FluxScheduler']['CoresPerSlotForFlux'])]
        argList += ["-N"]
        argList += [str(configStruct['FluxScheduler']['NodesPerJobForFlux'])]
        launchJobScript("flux", jobFile, True, extraArgs=argList)
    else:
        raise Exception('Using Unsupported Scheduler Mode')

def buildAndLaunchFGSJob(configStruct, rank, uname, reqid, fgsArgs, glueMode):
    solverCode = configStruct['solverCode']
    tag = configStruct['tag']
    dbPath = configStruct['dbFileName']
    lammps = configStruct['LAMMPSPath']
    if solverCode == SolverCode.BGK or solverCode == SolverCode.BGKMASSES:
        # Mkdir ./${TAG}_${RANK}_${REQ}
        outDir = tag + "_" + str(rank) + "_" + str(reqid)
        outPath = os.path.join(os.getcwd(), outDir)
        if(not os.path.exists(outPath)):
            os.mkdir(outPath)
            # cp ${SCRIPT_DIR}/lammpsScripts/${lammpsScript}
            # Copy scripts and configuration files
            pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
            jobEnvPath = os.path.join(pythonScriptDir, "envScripts")
            # Job files
            prepJobEnv(outPath, jobEnvPath,  configStruct)
            bgkResultScript = os.path.join(pythonScriptDir, "processBGKResult.py")
            # Generate input files
            lammpsScripts = writeBGKLammpsInputs(fgsArgs, outPath, glueMode)
            # Generate job script by writing to file
            # TODO: Identify a cleaner way to handle QOS and accounts and all the fun slurm stuff?
            # TODO: DRY this
            scriptFPath = os.path.join(outPath, tag + "_" + str(rank) + "_" + str(reqid) + ".sh")
            with open(scriptFPath, 'w') as slurmFile:
                # Make Header
                jobScriptBoilerplate(slurmFile, outDir, configStruct)
                slurmFile.write("cd " + outPath + "\n")
                slurmFile.write("source ./jobEnv.sh\n")
                # Set LAMMPS_BIN
                lammpsProvisioningBoilerplate(slurmFile, configStruct)
                # Actually call lammps
                for lammpsScript in lammpsScripts:
                    slurmFile.write("${LAUNCHER_BIN} ${JOB_DISTR_ARGS} ${LAMMPS_BIN} < " + lammpsScript + " \n")
                # And delete unnecessary files to save disk space
                slurmFile.write("rm ./profile.*.dat\n")
                # Process the result and write to DB
                slurmFile.write("`which python3` " + bgkResultScript + " -t " + tag + " -r " + str(rank) + " -i " + str(reqid) + " -d " + os.path.realpath(dbPath) + " -m " + str(glueMode.value) + " -c " + str(solverCode.value) + "\n")
                slurmFile.write("\n")
            #Chmod+x that script
            st = os.stat(scriptFPath)
            os.chmod(scriptFPath, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            # either syscall or subprocess.run slurm with the script
            launchFGSJob(scriptFPath, configStruct)
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

def insertALPrediction(dbPath, inFGS, outFGS, solverCode):
    if solverCode == SolverCode.BGK:
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKALLOGS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = (inFGS.Temperature,) + tuple(inFGS.Density) + tuple(inFGS.Charges) + (getGroundishTruthVersion(solverCode),) + (outFGS.Viscosity, outFGS.ThermalConductivity) + tuple(outFGS.DiffCoeff) + (getGroundishTruthVersion(solverCode),)
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    else:
        raise Exception("Using Unsupported Solver Code")

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
        (output,err) = self.model(inputStruct)
        modErr = self.model.iserrok(err)
        isLegit = simpleALErrorChecker(modErr)
        return (isLegit, output)

def insertResult(rank, tag, dbPath, reqid, fgsResult, resultProvenance):
    if isinstance(fgsResult, BGKOutputs):
        sqlDB = sqlite3.connect(dbPath, timeout=60.0)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    elif isinstance(fgsResult, BGKMassesOutputs):
        sqlDB = sqlite3.connect(dbPath, timeout=60.0)
        sqlCursor = sqlDB.cursor()
        insString = "INSERT INTO BGKMASSESRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()
    else:
        raise Exception('Using Unsupported Solver Code')

def queueFGSJob(configStruct, uname, reqID, inArgs, rank, modeSwitch):
    tag = configStruct['tag']
    dbPath = configStruct['dbFileName']
    # This is a brute force call. We only want an exact LAMMPS result
    # So first, check if we have already processed this request
    outFGS = None
    selQuery = getGNDStringAndTuple(inArgs, configStruct)
    sqlDB = sqlite3.connect(dbPath)
    sqlCursor = sqlDB.cursor()
    for row in sqlCursor.execute(selQuery[0], selQuery[1]):
        if isinstance(inArgs, BGKInputs):
            if row[22] == getGroundishTruthVersion(SolverCode.BGK):
                outFGS = BGKOutputs(Viscosity=row[10], ThermalConductivity=row[11], DiffCoeff=row[12:22])
        elif isinstance(inArgs, BGKMassesInputs):
            if row[26] == getGroundishTruthVersion(SolverCode.BGKMASSES):
                outFGS = BGKMassesOutputs(Viscosity=row[14], ThermalConductivity=row[15], DiffCoeff=row[16:26])
    if outFGS != None:
        # We had a hit, so send that
        insertResult(rank, tag, dbPath, reqID, outFGS, ResultProvenance.DB)
    else:
        # Nope, so now we see if we need an FGS job
        if useAnalyticSolution(inArgs):
            # It was, so let's get that solution
            results = getAnalyticSolution(inArgs)
            insertResult(rank, tag, dbPath, reqID, results, ResultProvenance.FGS)
        else:
            # Call fgs with args as scheduled job
            # job will write result back
            launchedJob = False
            while(launchedJob == False):
                queueJob = getQueueUsability(uname, configStruct)
                if queueJob == True:
                    print("Processing REQ=" + str(reqID))
                    buildAndLaunchFGSJob(configStruct, rank, uname, reqID, inArgs, modeSwitch)
                    launchedJob = True

def useAnalyticSolution(inputStruct):
    if isinstance(inputStruct, BGKInputs):
        # Diaw, put the checks here
        lammpsDens = np.array(inputStruct.Density)
        lammpsTemperature = inputStruct.Temperature
        lammpsIonization = np.array(inputStruct.Charges)
        Z = sum(lammpsIonization*lammpsDens)/sum(lammpsDens)
        a = (3./(4*np.pi*sum(lammpsDens))**(1./3.))
        eSq = 1.44e-7
        T = lammpsTemperature
        Gamma = Z*Z*eSq/a/T     #unitless
        if Gamma <= 0.1:
            return True
        else:
            return False
    else:
        return False

def getAnalyticSolution(inArgs):
    if isinstance(inArgs, BGKInputs):
        (cond, visc, diffCoeff) = ICFAnalytical_solution(inArgs.Density, inArgs.Charges, inArgs.Temperature)
        bgkOutput = BGKOutputs(Viscosity=visc, ThermalConductivity=cond, DiffCoeff=diffCoeff)
        return bgkOutput
    else:
        raise Exception('Using Unsupported Analytic Solver')

def pollAndProcessFGSRequests(configStruct, uname):
    numRanks = configStruct['ExpectedMPIRanks']

    defaultMode = configStruct['glueCodeMode']
    dbPath = configStruct['dbFileName']
    tag = configStruct['tag']
    packetType = configStruct['solverCode']
    alBackend = configStruct['alBackend']
    GNDthreshold = configStruct['ActiveLearningVariables']['GNDthreshold']
    numALRequesters = -1 * configStruct['ActiveLearningVariables']['NumberOfRequestingActiveLearners']

    reqNumArr = [0] * (numRanks + 1)

    #Spin until file exists
    while not os.path.exists(dbPath):
        time.sleep(1)
    #Get starting GNDCount of 0
    GNDcnt = 0
    #And start the glue loop
    keepSpinning = True
    while keepSpinning:
        # logic to not hammer DB/learner with unnecessary requests
        nuGNDcnt = getGNDCount(dbPath, packetType)
        if (nuGNDcnt - GNDcnt) > GNDthreshold or GNDcnt == 0:
            with open('alLog.out', 'w') as alOut, open('alLog.err', 'w') as alErr:
                with redirect_stdout(alOut), redirect_stdout(alErr):
                    interpModel = getInterpModel(packetType, alBackend, dbPath)
            GNDcnt = nuGNDcnt
        for i in range(numALRequesters, numRanks):
            rank = i
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
                if modeSwitch == ALInterfaceMode.FGS or modeSwitch == ALInterfaceMode.FASTFGS:
                    # Submit as LAMMPS job
                    queueFGSJob(configStruct, uname, task[0], task[1], rank, modeSwitch)
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
                    insertALPrediction(dbPath, task[1], output, packetType)
                    if isLegit:
                        insertResult(rank, tag, dbPath, task[0], output, ResultProvenance.ACTIVELEARNER)
                    else:
                        queueFGSJob(configStruct, uname, task[0], task[1], rank, ALInterfaceMode.FGS)
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
                elif modeSwitch == ALInterfaceMode.ANALYTIC:
                    if packetType == SolverCode.BGK:
                        # TODO: Probably verify there are only two species
                        if task[1].Density[2] != 0.0 or task[1].Density[3] != 0.0:
                            raise Exception('Using Analytic ICF with more than two species')
                        (cond, visc, diffCoeff) = ICFAnalytical_solution(task[1].Density, task[1].Charges, task[1].Temperature)
                        bgkOutput = BGKOutputs(Viscosity=visc, ThermalConductivity=cond, DiffCoeff=diffCoeff)
                        # Write the result
                        insertResult(rank, tag, dbPath, task[0], bgkOutput, ResultProvenance.ANALYTIC)
                    else:
                        raise Exception('Using Unsupported Analytic Solution')
                elif modeSwitch == ALInterfaceMode.KILL:
                    keepSpinning = False

if __name__ == "__main__":
    configStruct = processGlueCodeArguments()

    uname =  getpass.getuser()
    # We will not pass in uname via the json file

    pollAndProcessFGSRequests(configStruct, uname)
