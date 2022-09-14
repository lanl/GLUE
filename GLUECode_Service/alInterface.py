from collections.abc import Iterable
import os
import stat
import shutil
import numpy as np
import time
import subprocess
import getpass
import sys
from glueCodeTypes import ALInterfaceMode, SolverCode, ResultProvenance, LearnerBackend, BGKInputs, BGKMassesInputs, BGKOutputs, BGKMassesOutputs, SchedulerInterface, ProvisioningInterface, DatabaseMode
from contextlib import redirect_stdout
from ICF_Utils import ICFAnalytical_solution, check_zeros_trace_elements
from glueArgParser import processGlueCodeArguments
from alDBHandlers import getDBHandle

def getGroundishTruthVersion(packetType):
    if packetType == SolverCode.BGK:
        return 2.2
    elif packetType == SolverCode.BGKMASSES:
        return 1.0
    else:
        raise Exception('Using Unsupported Solver Code')

def getSelString(packetType, latestID, missingIDs):
    # TODO: Make this smarter
    minID = 0
    if len(missingIDs) == 0:
        minID = latestID + 1
    else:
        minID = min(missingIDs)
    if packetType == SolverCode.BGK:
        return "SELECT * FROM BGKREQS WHERE RANK=? AND REQ>=" + str(minID) + "  AND TAG=?;"
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
    else:
        raise Exception('Using Unsupported Solver Code')

def getEquivalenceSQLStringsResults(packetType, dbKey):
    if packetType == SolverCode.BGK:
        globalTable = dbKey + ".BGKRESULTS"
        localTable = "BGKRESULTS"
        # We just need reqid, rank, and tag to match
        selString = ""
        selString += globalTable + ".TAG="
        selString += localTable + ".TAG"
        selString += " AND "
        selString += globalTable + ".RANK="
        selString += localTable + ".RANK"
        selString += " AND "
        selString += globalTable + ".REQ="
        selString += localTable + ".REQ"
        return selString
    else:
        raise Exception('Using Unsupported Solver Code')

def getEquivalenceSQLStringsGND(packetType, dbKey):
    if packetType == SolverCode.BGK:
        globalTable = dbKey + ".BGKGND"
        localTable = "BGKGND"
        selString = ""
        # We will match on Request Info
        selString += globalTable + ".TEMPERATURE="
        selString += localTable + ".TEMPERATURE"
        selString += " AND "
        for i in range(4):
            selString += globalTable + ".DENSITY_" + str(i) + "="
            selString += localTable + ".DENSITY_" + str(i)
            selString += " AND "
            selString += globalTable + ".CHARGES_" + str(i) + "="
            selString += localTable + ".CHARGES_" + str(i)
            selString += " AND "
        # And inversion just for safety reasons
        selString += globalTable + ".INVERSION="
        selString += localTable + ".INVERSION"
        return selString
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

def checkFluxQueue():
    try:
        runproc = subprocess.run(
            ["flux", "jobs"],
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
        else:
            return False
    elif configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        return True
    elif configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        queueState = getFluxQueue()
        maxJobs = configStruct['FluxScheduler']['ConcurrentJobs']
        if queueState[0] < maxJobs:
            return True
        else:
            return False
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

def getFluxQueue():
    fluxOut = checkFluxQueue()
    if fluxOut == "":
        return (sys.maxsize, [])
    strList = fluxOut.splitlines()
    if len(strList) > 1:
        return (len(strList) - 1, strList[1:])
    else:
        return (0, [])

# TODO: Make sure this is all from the fine grain table, not coarse grain, because wow
def getAllGNDData(dbHandle, solverCode):
    selString = ""
    if solverCode == SolverCode.BGK:
        selString = "SELECT * FROM BGKGND;"
    else:
        raise Exception('Using Unsupported Solver Code')
    dbHandle.openCursor()
    gndResults = []
    for row in dbHandle.execute(selString):
        # Add row to numpy array
        gndResults.append(row)
    dbHandle.closeCursor()
    return np.array(gndResults)

def getGNDCount(dbHandle, solverCode):
    selString = ""
    if solverCode == SolverCode.BGK:
        selString = "SELECT COUNT(*)  FROM BGKGND;"
    else:
        raise Exception('Using Unsupported Solver Code')
    dbHandle.openCursor()
    numGND = 0
    for row in dbHandle.execute(selString):
        # Should just be one row with one value
        numGND = row[0]
    dbHandle.closeCursor()
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
        if 'ManualProvisioning' in configStruct and 'LAMMPSPath' in configStruct['ManualProvisioning']:
            jobFile.write("\texport LAMMPS_BIN=" + configStruct['ManualProvisioning']['LAMMPSPath'] + "\n")
        else:
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
    # Fine grain so want to use the slower shared DB
    dbPath = configStruct['DatabaseSettings']['FineGrainDB']['DatabaseURL']
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
                # First, make the arguments
                argList = ""
                argList += " -t " + tag
                argList += " -r " + str(rank)
                argList += " -i " + str(reqid)
                argList += " -d " + os.path.realpath(dbPath)
                argList += " -m " + str(glueMode.value)
                argList += " -c " + str(solverCode.value)
                fgDBStruct = configStruct['DatabaseSettings']['FineGrainDB']
                argList += " -b " + str(int(fgDBStruct['DatabaseMode']))
                if "DatabaseUser" in fgDBStruct:
                    argList += "- u " + fgDBStruct["DatabaseUser"]
                if "DatabasePassword" in fgDBStruct:
                    argList += "- p " + fgDBStruct["DatabasePassword"]
                # Pass args to script
                slurmFile.write("`which python3` " + bgkResultScript
                    + argList
                    + "\n")
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

def getInterpModel(packetType, alBackend, dbHandle):
    #TODO Use packetType
    if alBackend == LearnerBackend.FAKE:
        return InterpModelWrapper(alModelStub, uqCheckerStub)
    if alBackend == LearnerBackend.PYTORCH:
        import nn_learner
        return BGKPytorchInterpModel(nn_learner.retrain(dbHandle))
    if alBackend == LearnerBackend.RANDFOREST:
        import rf_learner
        return BGKRandForestInterpModel(rf_learner.retrain(dbHandle)) 
    else:
        raise Exception('Using Unsupported Active Learning Backewnd')

def insertALPrediction(inFGS, outFGS, solverCode, sqlDB):
    if solverCode == SolverCode.BGK:
        sqlDB.openCursor()
        insString = "INSERT INTO BGKALLOGS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = (inFGS.Temperature,) + tuple(inFGS.Density) + tuple(inFGS.Charges) + (getGroundishTruthVersion(solverCode),) + (outFGS.Viscosity, outFGS.ThermalConductivity) + tuple(outFGS.DiffCoeff) + (getGroundishTruthVersion(solverCode),)
        sqlDB.execute(insString, insArgs)
        sqlDB.commit()
        sqlDB.closeCursor()
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

class BGKRandForestInterpModel(InterpModelWrapper):
        def __init__(self, newModel):
            # TODO: Asynchrony!
            self.model = newModel
        def __call__(self, inputStruct):
            (output,err) = self.model(inputStruct)
            modErr = self.model.iserrok(err)
            isLegit = simpleALErrorChecker(modErr)
            return (isLegit, output)

def insertResultSlow(rank, tag, reqid, fgsResult, resultProvenance, sqlDB):
    if isinstance(fgsResult, BGKOutputs):
        sqlDB.openCursor()
        insString = "INSERT INTO BGKRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        sqlDB.execute(insString, insArgs)
        sqlDB.commit()
        sqlDB.closeCursor()
    else:
        raise Exception('Using Unsupported Solver Code')

def insertResult(rank, tag, reqid, fgsResult, resultProvenance, sqlDB):
    if isinstance(fgsResult, BGKOutputs):
        sqlDB.openCursor()
        insString = "INSERT INTO BGKFASTRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        sqlDB.execute(insString, insArgs)
        sqlDB.commit()
        sqlDB.closeCursor()
    else:
        raise Exception('Using Unsupported Solver Code')

#TODO: Figure out correct location for this
def icfComparator(lhs, rhs, epsilon):
    retVal = True
    if rhs.Temperature != 0.0 and (lhs.Temperature - rhs.Temperature) / rhs.Temperature > epsilon:
        retVal = False
    for i in range(4):
        if rhs.Density[i] != 0.0 and (lhs.Density[i] - rhs.Density[i]) / rhs.Density[i] > epsilon:
            return False
        if rhs.Charges[i] != 0.0 and (lhs.Charges[i] - rhs.Charges[i]) / rhs.Charges[i] > epsilon:
            return False
    return retVal

def cacheCheck(inArgs, configStruct, dbCache):
    if isinstance(inArgs, BGKInputs):
        #TODO: Make this cleaner
        epsilon = configStruct['ICFParameters']['RelativeError']
        for entry in dbCache:
            if icfComparator(inArgs, entry[0], epsilon):
                return entry[1]
        return None
    else:
        return None

def mergeBufferTable(solverCode, cgDB):
    if solverCode == SolverCode.BGK:
        cgDB.openCursor()
        mergeStr = "INSERT INTO BGKRESULTS SELECT * FROM BGKFASTRESULTS;"
        delStr = "DELETE FROM BGKFASTRESULTS;"
        cgDB.execute(mergeStr)
        cgDB.execute(delStr)
        cgDB.commit()
        cgDB.closeCursor()
    else:
        raise Exception('Using Unsupported Solver Code')

#TODO: We do not actually pull GND. Just Results. Check if that is okay. It probably isn't
def pullGlobalResultsToFastDBPython(solverCode, cgDB, fgDB):
    # Manually copy data in by opening the DB, reading it, and then writing results
    if solverCode == SolverCode.BGK:
        # Open Fine Grain DB
        fgDB.openCursor()
        # Copy out results
        resultList = []
        # TODO: Add logic to reduce number of reads later...
        #   Might be able to do an SQL query to find the gap
        resQuery = "SELECT * FROM BGKRESULTS;"
        for row in fgDB.execute(resQuery):
            # Basically just copy the result verbatim into list
            resultList.append(row)
        # Close FGDB
        fgDB.closeCursor()
        # Write results to fastDB (CGDB)
        if len(resultList) > 0:
            cgDB.openCursor()
            # TODO: Update to do bulk insertions once this works
            for result in resultList:
                insString = "INSERT INTO BGKRESULTS (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"
                cgDB.execute(insString, tuple(result))
            cgDB.commit()
            cgDB.closeCursor()
    else:
        raise Exception('pullGlobalResultsToFastDBPython: Using Unsupported Solver Code')

def pullGlobalResultsToFastDBAttach(solverCode, cgDB, fgDB):
    raise Exception('pullGlobalResultsToFastDBAttach: Currently Unsupported')
    # Might need to add to fine grain db path  because of different dirs?
    #TODO: Probably do two approaches
    #  1. If both DB types are the same, attach?
    #  2. if DB types differ... we take a memory hit?
    dbAlias = "DBFG"
    if solverCode == SolverCode.BGK:
        #TODO: Probably go through all of this because we mixed up fast and fine grain a few times
        #TODO: Also may need to still handle this special as we are re-opening a DB
        #TODO: Maybe add another command to the class?
        #WARNING WARNING WARNING: THis is gonna be an issue with different DB types...

        # Probably still have fastDB open?
        sqlCursor = fastDB.cursor()
        # Want to ATTACH globalDB to existing connection
        sqlAttachStr = "ATTACH DATABASE \'" + fgDBPath
        sqlAttachStr += "\' AS " + dbAlias + ";"
        sqlCursor.execute(sqlAttachStr)
        # Now copy out the results
        sqlResultsStr = "INSERT INTO BGKRESULTS SELECT * FROM "
        sqlResultsStr += dbAlias + ".BGKRESULTS WHERE NOT EXISTS("
        sqlResultsStr += "SELECT * FROM BGKRESULTS WHERE("
        sqlResultsStr += getEquivalenceSQLStringsResults(solverCode, dbAlias)
        sqlResultsStr += "));"
        sqlCursor.execute(sqlResultsStr)
        # And the GNDish truth
        sqlGNDStr = "INSERT INTO BGKGND SELECT * FROM "
        sqlGNDStr += dbAlias + ".BGKGND WHERE NOT EXISTS("
        sqlGNDStr += "SELECT * FROM BGKGND WHERE("
        sqlGNDStr += getEquivalenceSQLStringsGND(solverCode, dbAlias)
        sqlGNDStr += "));"
        sqlCursor.execute(sqlGNDStr)
        fastDB.commit()
        # And detach the DB
        sqlDetachStr = "DETACH DATABASE ?;"
        sqlDetachTup = (dbAlias,)
        sqlCursor.execute(sqlDetachStr, sqlDetachTup)
        # Commit commands and close cursor
        fastDB.commit()
        sqlCursor.close()
    else:
        raise Exception('pullGlobalResultsToFastDBAttach: Using Unsupported Solver Code')

def queueFGSJob(configStruct, uname, reqID, inArgs, rank, modeSwitch, cgDB, fgDB, dbCache):
    tag = configStruct['tag']
    # This is a brute force call. We only want an exact LAMMPS result
    outFGS = None
    # So first, check if we have already found a DB hit on a previous query
    outFGS = cacheCheck(inArgs, configStruct, dbCache)
    # If no hit, we check the DB
    if outFGS == None:
        selQuery = getGNDStringAndTuple(inArgs, configStruct)
        fgDB.openCursor()
        for row in fgDB.execute(selQuery[0], selQuery[1]):
            if isinstance(inArgs, BGKInputs):
                if row[22] == getGroundishTruthVersion(SolverCode.BGK):
                    outFGS = BGKOutputs(Viscosity=row[10], ThermalConductivity=row[11], DiffCoeff=row[12:22])
            elif isinstance(inArgs, BGKMassesInputs):
                if row[26] == getGroundishTruthVersion(SolverCode.BGKMASSES):
                    outFGS = BGKMassesOutputs(Viscosity=row[14], ThermalConductivity=row[15], DiffCoeff=row[16:26])
        fgDB.closeCursor()
        # Did we get a hit?
        if outFGS != None:
            # Put it in the DBCache for later
            #TODO: Cap the size of this cache
            dbCache.append((inArgs, outFGS))
    #Did we get a hit from either?
    if outFGS != None:
        # We had a hit, so send that
        insertResult(rank, tag, reqID, outFGS, ResultProvenance.DB, cgDB)
    else:
        # Nope, so now we see if we need an FGS job
        if useAnalyticSolution(inArgs):
            # It was, so let's get that solution
            results = getAnalyticSolution(inArgs)
            insertResult(rank, tag, reqID, results, ResultProvenance.FGS, cgDB)
            # TODO: Apparently we never wrote valid analytic solutions to ground truth table
            #  Do we want to? Probably?
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
    tag = configStruct['tag']
    packetType = configStruct['solverCode']
    alBackend = configStruct['alBackend']
    GNDthreshold = configStruct['ActiveLearningVariables']['GNDthreshold']
    numALRequesters = configStruct['ActiveLearningVariables']['NumberOfRequestingActiveLearners']

    # One task queue to rule them (the ranks) all
    taskQueue = []
    # Array to handle missing requests
    reqArray = [[i-numALRequesters, -1, []] for i in range(0, numRanks + numALRequesters)]
    # Cache for DB hits
    dbCache = []

    #Set up database handles
    cgDBSettings = configStruct['DatabaseSettings']['CoarseGrainDB']
    cgDB = getDBHandle(cgDBSettings, True)
    fgDBSettings = configStruct['DatabaseSettings']['FineGrainDB']
    fgDB = getDBHandle(fgDBSettings)

    #Get starting GNDCount of 0
    GNDcnt = 0
    #And start the glue loop
    keepSpinning = True
    print("Starting Loop")
    while keepSpinning:
        #print("Loop Iter")
        #Logic to not hammer DB/learner with unnecessary retraining requests
        # TODO: Ground truths from fine grain, not coarse grain
        nuGNDcnt = getGNDCount(fgDB, packetType)
        if defaultMode == ALInterfaceMode.ACTIVELEARNER and ((nuGNDcnt - GNDcnt) > GNDthreshold or GNDcnt == 0):
            with open('alLog.out', 'w') as alOut, open('alLog.err', 'w') as alErr:
                with redirect_stdout(alOut), redirect_stdout(alErr):
                    interpModel = getInterpModel(packetType, alBackend, fgDB)
            GNDcnt = nuGNDcnt
        #Now populate the task queue
        for i in range(0, numRanks + numALRequesters):
            rank = reqArray[i][0]
            latestID = reqArray[i][1]
            missingIDs = reqArray[i][2]
            selString = getSelString(packetType, latestID, missingIDs)
            selArgs = (rank, tag)
            resultQueue = []
            # SELECT request
            cgDB.openCursor()
            for row in cgDB.execute(selString, selArgs):
                # Process row for later
                (solverInput, reqType) = processReqRow(row, packetType)
                # (reqID, alMode, inputTuple)
                resultQueue.append((row[2], reqType, solverInput))
            cgDB.closeCursor()
            #Get latest received request ID
            if len(resultQueue) > 0:
                newLatestID = max(resultQueue, key=lambda i: i[0])[0]
                #If that latest ID is more laterest than our old latest
                if newLatestID > latestID:
                    # Add what we were missing
                    missingIDs += range(latestID+1, newLatestID+1)
                    # And update latestID
                    reqArray[i][1] = newLatestID
                #And then process those results
                for result in resultQueue:
                    # Were we looking for this?
                    if result[0] in missingIDs:
                        # We were, so lets queue it
                        #Format is (rank, reqID, alMode, inputTuple)
                        newTask = (rank, result[0], result[1], result[2])
                        taskQueue.append(newTask)
                        missingIDs.remove(result[0])
        #And now we process that task queue
        #TODO: Refactor slurm/flux queue logic up to here for throttling active jobs
        for task in taskQueue:
            # A shim to reuse old logic
            rank = task[0]
            reqID = task[1]
            requestedMode = task[2]
            taskArgs = task[3]
            # Process tasks based on mode
            modeSwitch = defaultMode
            if requestedMode != ALInterfaceMode.DEFAULT:
                modeSwitch = requestedMode
            if modeSwitch == ALInterfaceMode.FGS or modeSwitch == ALInterfaceMode.FASTFGS:
                # Submit as LAMMPS job
                queueFGSJob(configStruct, uname, reqID, taskArgs, rank, modeSwitch, cgDB, fgDB, dbCache)
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
                (isLegit, output) = interpModel(taskArgs)
                insertALPrediction(taskArgs, output, packetType, cgDB)
                if isLegit:
                    insertResult(rank, tag, reqID, output, ResultProvenance.ACTIVELEARNER, cgDB)
                else:
                    queueFGSJob(configStruct, uname, reqID, taskArgs, rank, ALInterfaceMode.FGS, cgDB, fgDB, dbCache)
            elif modeSwitch == ALInterfaceMode.FAKE:
                if packetType == SolverCode.BGK:
                    # Simplest stencil imaginable
                    bgkInput = taskArgs
                    bgkOutput = BGKOutputs(Viscosity=0.0, ThermalConductivity=0.0, DiffCoeff=[0.0]*10)
                    bgkOutput.DiffCoeff[7] = (bgkInput.Temperature + bgkInput.Density[0] +  bgkInput.Charges[3]) / 3
                    # Write the result
                    insertResult(rank, tag, reqID, bgkOutput, ResultProvenance.FAKE, cgDB)
                else:
                    raise Exception('Using Unsupported Solver Code')
            elif modeSwitch == ALInterfaceMode.ANALYTIC:
                if packetType == SolverCode.BGK:
                    # TODO: Probably verify there are only two species
                    if taskArgs.Density[2] != 0.0 or taskArgs.Density[3] != 0.0:
                        raise Exception('Using Analytic ICF with more than two species')
                    (cond, visc, diffCoeff) = ICFAnalytical_solution(taskArgs.Density, taskArgs.Charges, taskArgs.Temperature)
                    bgkOutput = BGKOutputs(Viscosity=visc, ThermalConductivity=cond, DiffCoeff=diffCoeff)
                    # Write the result
                    insertResult(rank, tag, reqID, bgkOutput, ResultProvenance.ANALYTIC, cgDB)
                else:
                    raise Exception('Using Unsupported Analytic Solution')
            elif modeSwitch == ALInterfaceMode.KILL:
                keepSpinning = False
        #And empty out the task queue....
        del(taskQueue[:])
        #And now merge and purge buffer tables
        #First we want to copy the fast local results to the right table of the shared db
        mergeBufferTable(SolverCode.BGK, cgDB)
        #And then copy in the coarse grain results
        pullGlobalResultsToFastDBPython(SolverCode.BGK, cgDB, fgDB)
    print("Loop Done")
    #Close SQL Connection
    cgDB.closeDB()
    fgDB.closeDB()

if __name__ == "__main__":
    configStruct = processGlueCodeArguments()

    uname =  getpass.getuser()
    # We will not pass in uname via the json file

    pollAndProcessFGSRequests(configStruct, uname)
