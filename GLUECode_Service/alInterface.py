from collections.abc import Iterable
import os
import stat
import shutil
import numpy as np
import subprocess
import getpass
import sys
from glueCodeTypes import ALInterfaceMode, SolverCode, ResultProvenance, LearnerBackend, BGKInputs, BGKMassesInputs, BGKOutputs, BGKMassesOutputs, SchedulerInterface, ProvisioningInterface
from contextlib import redirect_stdout
from ICF_Utils import ICFAnalytical_solution, check_zeros_trace_elements, icfComparator
from glueArgParser import processGlueCodeArguments
from alDBHandlers import getDBHandle

def getGroundishTruthVersion(packetType):
    """Get version number associated with packet type

    Function to reconcile significant changes with data generation or storage types to avoid interpolation errors

    Args:
        packetType (SolverCode): SolverCode enum corresponding to application

    Raises:
        Exception: If using unsupported SolverCode enum

    Returns:
        float: Version number of generated fine grain results
    """
    if packetType == SolverCode.BGK:
        return 2.2
    elif packetType == SolverCode.BGKMASSES:
        return 1.0
    else:
        raise Exception('Using Unsupported Solver Code')

def getSelString(packetType, latestID, missingIDs):
    """Generate 'SELECT' string for SQL query on missing results

    Generates a 'SELECT' string to pass to SQL in the event that not all data points
    were available when the previous 'SELECT' command returned.

    Args:
        packetType (SolverCode): SolverCode enum corresponding to application
        latestID (int): Highest ID value of currently received results
        missingIDs (list): List of currently missing ID values

    Raises:
        Exception: If using unsupported SolverCode enum

    Returns:
        str: 'SELECT' string to request missing IDs
    """
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
    """Generate 'SELECT' request for GND truth within specified tolerances

    Args:
        fgsArgs: Arguments for fine grain simulation
        configStruct: Dictionary containing configuration data for simulation

    Raises:
        Exception: If using unsupported fine grain simulation arguments types

    Returns:
        'SELECT' request (string and arguments tuple) for GND truth within specified tolerances
    """
    selString = ""
    selTup = ()
    if isinstance(fgsArgs, BGKInputs):
        # Percent error acceptable for a match
        relError = configStruct['ICFParameters']['RelativeError']
        # TODO: DRY this for later use
        selString += "SELECT * FROM BGKGND WHERE "
        #Temperature
        if(fgsArgs.Temperature != 0.0):
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
    """Process SQL request row into fine grain simulation tuple

    Args:
        sqlRow (list): SQL Row returned by `SELECT` command
        packetType (SolverCode): SolverCode enum corresponding to application

    Raises:
        Exception: If using unsupported SolverCode enum

    Returns:
        tuple: Fine grain simulation arguments and how the GLUE Code should handle it
    """
    if packetType == SolverCode.BGK:
        #Process row to arguments
        bgkInput = BGKInputs(Temperature=float(sqlRow[3]), Density=[], Charges=[])
        bgkInput.Density.extend([sqlRow[4], sqlRow[5], sqlRow[6], sqlRow[7]])
        bgkInput.Charges.extend([sqlRow[8], sqlRow[9], sqlRow[10], sqlRow[11]])
        reqType = ALInterfaceMode(sqlRow[12])
        return (bgkInput, reqType)
    else:
        raise Exception('Using Unsupported Solver Code')

def writeBGKLammpsInputs(fgsArgs, dirPath, glueMode):
    """Write files for LAMMPS runs for ICF Simulations

    Args:
        fgsArgs: Argumentrs for fine grain simulation
        dirPath: Directory to write configuration files in
        glueMode (ALInterfaceMode): Type of LAMMPS simulation to run

    Raises:
        Exception: Unsupported ALInterfaceMode
        Exception: Unsupported fine grain simulation arguments type

    Returns:
        List of LAMMPS scripts to execute as part of fine grain simulation
    """
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
    """Check Slurm Queue for number of running jobs

    Args:
        uname (str): UID of user running GLUE Code

    Returns:
        String output of active slurm jobs for that UID
    """
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
    """Check Flux Queue for number of running jobs

    Returns:
        String output of active flux jobs
    """
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
    """Launch fine grain simulation's job script

    Args:
        binary (str): Job scheduler binary to call
        script (str): The path to the job script to run
        wantReturn (bool): Indicate if the output of the job submission should be returned
        extraArgs (list, optional): Additional arguments to pass to the job scheduler. Defaults to [].

    Returns:
        str: Empty strng or the output of the command
    """
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
    """Check if queue is (over)saturated with jobs

    Args:
        uname (str): UID of user running GLUE Code
        configStruct: Dictionary containing configuration data for simulation

    Raises:
        Exception: Using Unsupported Scheduler Mode

    Returns:
        bool: Bool indicating if the scheduler is not saturated
    """
    if configStruct['SchedulerInterface'] == SchedulerInterface.SLURM:
        queueState = getNumberOfJobsInSlurmQueue(uname)
        maxJobs = configStruct['SlurmScheduler']['MaxSlurmJobs']
        if queueState[0] < maxJobs:
            return True
        else:
            return False
    elif configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        return True
    elif configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        queueState = getNumberOfJobsInFluxQueue()
        maxJobs = configStruct['FluxScheduler']['ConcurrentJobs']
        if queueState[0] < maxJobs:
            return True
        else:
            return False
    else:
        raise Exception('Using Unsupported Scheduler Mode')

def getNumberOfJobsInSlurmQueue(uname):
    """Get the number of active jobs for this UID in the slurm queue

    Args:
        uname (str): UID of user running GLUE Code

    Returns:
        int: Number of slurm jobs in queue
    """
    slurmOut = checkSlurmQueue(uname)
    if slurmOut == "":
        return (sys.maxsize, [])
    strList = slurmOut.splitlines()
    if len(strList) > 1:
        return (len(strList) - 1, strList[1:])
    else:
        return (0, [])

def getNumberOfJobsInFluxQueue():
    """Get the number of active jobs in the flux queue

    Returns:
        int: Number of flux jobs in queue
    """
    fluxOut = checkFluxQueue()
    if fluxOut == "":
        return (sys.maxsize, [])
    strList = fluxOut.splitlines()
    if len(strList) > 1:
        return (len(strList) - 1, strList[1:])
    else:
        return (0, [])

def getAllGNDData(dbHandle, solverCode):
    """Generate list of all data in GND table

    Args:
        dbHandle (ALDBHandle): Object to access database
        solverCode (SolverCode): SolverCode enum corresponding to simulation

    Raises:
        Exception: Using Unsupported Solver Code

    Returns:
        numpy.array: Numpy array of all ground truth data
    """
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
    """Get number of GND entries in table for simulation

    Args:
        dbHandle (ALDBHandle): Object to access database
        solverCode (SolverCode): SolverCode enum corresponding to simulation

    Raises:
        Exception: Using Unsupported Solver Code

    Returns:
        int: Numer of GND truth entries in table for simulation
    """
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
    """Generates boilerplate/headers of job scripts

    Args:
        jobFile: File handle to write job script to
        outDir (str): Path to output directory
        configStruct: Dictionary containing configuration data for simulation

    Raises:
        Exception: Unsupported SchedulerInterface
    """
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
        jobFile.write("export LAUNCHER_BIN=\"flux mini run\"\n")
        jobFile.write("export JOB_DISTR_ARGS=\"" + \
            "-N " + str(configStruct['FluxScheduler']['NodesPerJobForFlux']) + \
            " -n " + str(configStruct['FluxScheduler']['SlotsPerJobForFlux']) + \
            " -c " + str(configStruct['FluxScheduler']['CoresPerSlotForFlux']) + \
            "\"\n")
    else:
        raise Exception('Using Unsupported Scheduler Mode')

def prepJobEnv(outPath, jobEnvPath, configStruct):
    """Copy in job environment script for job script

    Args:
        outPath (str): Path to run directory for job script
        jobEnvPath (str): Path to job environment script directory
        configStruct: Dictionary containing configuration data for simulation
    """
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
    """Generate boilerplate bash script to privision LAMMPS

    Args:
        jobFile: File handle to write job script to
        configStruct: Dictionary containing configuration data for simulation

    Raises:
        Exception: Unsupported ProvisioningInterface specified
    """
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
        # TODO: Generalize this to support more than just MPI
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
    """Launch/queue fine grain simulation

    Args:
        jobFile: File handle to write job script to
        configStruct: Dictionary containing configuration data for simulation

    Raises:
        Exception: Unsupported SchedulerInterface specified
    """
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

def buildAndLaunchFGSJob(configStruct, rank, reqid, fgsArgs, glueMode):
    """Build and launch fine grain simulation for specified arguments

    Args:
        configStruct: Dictionary containing configuration data for simulation
        rank: Identifier of job originator. Commonly MPI rank
        reqid: Monotonically increasing ID to use as job ID to look up result later
        fgsArgs: Arguments for fine grain simulation
        glueMode (ALInterfaceMode): Type of fine grain simulation to run

    Raises:
        Exception: Using unsupported SolverCode
    """
    solverCode = configStruct['solverCode']
    tag = configStruct['tag']
    # Fine grain so want to use the slower shared DB
    dbPath = configStruct['DatabaseSettings']['FineGrainDB']['DatabaseURL']
    if solverCode == SolverCode.BGK or solverCode == SolverCode.BGKMASSES:
        # mkdir ./${TAG}_${RANK}_${REQ}
        outDir = tag + "_" + str(rank) + "_" + str(reqid)
        outPath = os.path.join(os.getcwd(), outDir)
        if(not os.path.exists(outPath)):
            os.mkdir(outPath)
            # cp ${SCRIPT_DIR}/lammpsScripts/${lammpsScript} .
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
    """Reference implementation for active learning model

    Reference implementation/stub for active learning model. Primarily used for debugging purposes.

    Args:
        inArgs: Fine grain simulation arguments

    Raises:
        Exception: Using Unsupported Solver Code With Interpolation Model

    Returns:
        tuple: Float corresponding to confidence in solution and output of fine grain simulation
    """
    if isinstance(inArgs, BGKInputs):
        bgkOutput = None
        return (sys.float_info.max, bgkOutput)
    else:
        raise Exception('Using Unsupported Solver Code With Interpolation Model')

def uqCheckerStub(err):
    """Reference implementation for uncertainty quantification checking

    Reference implementation/stub for uncertainty quantification evaluation. Primarily used for debugging purposes.

    Args:
        err (float): Reported uncertainty from active learning model

    Returns:
        bool: Bool corresponding to if this is considered a valid result
    """
    if err < sys.float_info.max:
        return True
    else:
        return False

def getInterpModel(packetType, alBackend, dbHandle):
    """Get interpolation model to use for active learning

    Args:
        packetType (SolverCode): Enum corresponding to simulation
        alBackend (LearnerBackend): Machine learning backend to use with active learning
        dbHandle (ALDBHandle): Object to access database

    Raises:
        Exception: Using Unsupported LearnerBackend

    Returns:
        InterpModelWrapper: Function object for active learner
    """
    #TODO Also switch on packetType
    if alBackend == LearnerBackend.FAKE:
        return InterpModelWrapper(alModelStub, uqCheckerStub)
    if alBackend == LearnerBackend.PYTORCH:
        from ML_Utils import nn_learner
        return MLModelWrapper(nn_learner.retrain(dbHandle))
    if alBackend == LearnerBackend.RANDFOREST:
        from ML_Utils import rf_learner
        return MLModelWrapper(rf_learner.retrain(dbHandle)) 
    else:
        raise Exception('Using Unsupported Active Learning Backend')

def insertALPrediction(inFGS, outFGS, solverCode, dbHandle):
    """Insert Active Learning Prediction into appropriate database

    Args:
        inFGS : Fine grain simulation inputs
        outFGS : Outputs generated through active learning
        solverCode (SolverCode): Enum corresponding to simulation
        dbHandle (ALDBHandle): Object to access database

    Raises:
        Exception: Using Unsupported SolverCode
    """
    if solverCode == SolverCode.BGK:
        dbHandle.openCursor()
        insString = "INSERT INTO BGKALLOGS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        insArgs = (inFGS.Temperature,) + tuple(inFGS.Density) + tuple(inFGS.Charges) + (getGroundishTruthVersion(solverCode),) + (outFGS.Viscosity, outFGS.ThermalConductivity) + tuple(outFGS.DiffCoeff) + (getGroundishTruthVersion(solverCode),)
        dbHandle.execute(insString, insArgs)
        dbHandle.commit()
        dbHandle.closeCursor()
    else:
        raise Exception("Using Unsupported Solver Code")

def simpleALErrorChecker(inputStruct):
    """Check if all active learning error checks passed

    Utility function provided to support AL models which 
    return a container of bools corresponding to each output.

    Args:
        inputStruct: Single bool or container of bools corresponding to uncertainty/error checks

    Returns:
        bool: Boolean indicating if this result is valid
    """
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
    """Function object to interface with interpolation models
    """
    def __init__(self, newModel, uqChecker):
        """Constructor for InterpModelWrapper

        Args:
            newModel: Function pointer for active learning model
            uqChecker: Function pointer for uncertainty quantification evaluation
        """
        self.model = newModel
        self.uq = uqChecker
    def __call__(self, inputStruct):
        """Operator() overload for InterpModelWrapper

        Generate result from specified input and indicate validity

        Args:
            inputStruct: Fine grain simulation input arguments

        Returns:
            tuple: Bool indicating if generated result is valid as well as generated result itself
        """
        (err, output) = self.model(inputStruct)
        isLegit = self.uq(err)
        return (isLegit, output)

class MLModelWrapper(InterpModelWrapper):
    """Implementation of InterpModelWrapper for more advanced machine learning models
    """
    def __init__(self, newModel):
        """Constructor for MLModelWrapper

        Args:
            newModel: Function pointer for active learning model with internal uncertainty quantification
        """
        # TODO: Asynchrony!
        self.model = newModel
    def __call__(self, inputStruct):
        """Operator() overload for MLModelWrapper

        Uses underlying model to generate a result and then evaluates uncertainty quantification of all fields to determine validity

        Args:
            inputStruct: Fine grain simulation input arguments

        Returns:
            tuple: Bool indicating if generated result is valid as well as generated result itself
        """
        (output,err) = self.model(inputStruct)
        modErr = self.model.iserrok(err)
        isLegit = simpleALErrorChecker(modErr)
        return (isLegit, output)

def insertResultSlow(rank, tag, reqid, fgsResult, resultProvenance, dbHandle):
    """Insert result into slower/primary results table

    Args:
        rank: Identifier of job originator. Commonly MPI rank
        tag (str): Identifier for this set of data
        reqid: Monotonically increasing ID to use as job ID to look up result later
        fgsResult: Result of fine grain simulation
        resultProvenance (ResultProvenance): Type of result being inserted
        dbHandle (ALDBHandle): Object to access database

    Raises:
        Exception: _description_
    """
    #TODO: Merge this with `insertResult`
    if isinstance(fgsResult, BGKOutputs):
        dbHandle.openCursor()
        insString = "INSERT INTO BGKRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        dbHandle.execute(insString, insArgs)
        dbHandle.commit()
        dbHandle.closeCursor()
    else:
        raise Exception('Using Unsupported Solver Code')

def insertResult(rank, tag, reqid, fgsResult, resultProvenance, dbHandle):
    """Insert result into faster/intermediate results table

    Args:
        rank: Identifier of job originator. Commonly MPI rank
        tag (str): Identifier for this set of data
        reqid: Monotonically increasing ID to use as job ID to look up result later_
        fgsResult: Result of fine grain simulation
        resultProvenance (ResultProvenance): Type of result being inserted
        dbHandle (ALDBHandle): Object to access database

    Raises:
        Exception: _description_
    """
    if isinstance(fgsResult, BGKOutputs):
        dbHandle.openCursor()
        insString = "INSERT INTO BGKFASTRESULTS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, rank, reqid, fgsResult.Viscosity, fgsResult.ThermalConductivity) + tuple(fgsResult.DiffCoeff) + (resultProvenance,)
        dbHandle.execute(insString, insArgs)
        dbHandle.commit()
        dbHandle.closeCursor()
    else:
        raise Exception('Using Unsupported Solver Code')

def cacheCheck(inArgs, configStruct, dbCache):
    """Check local in-memory cache for similar requests

    Args:
        inArgs: Fine grain simulation arguments
        configStruct: Dictionary containing configuration data for simulation
        dbCache: Container used for local cache of requests and results

    Returns:
        Result if found. None otherwise
    """
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
    """Merge FAST and normal result tables in database

    Args:
        solverCode (SolverCode): Enum corresponding to simulation
        cgDB (ALDBHandle): Object to access (coarse grain) database

    Raises:
        Exception: Using Unsupported SolverCode
    """
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

def pullGlobalResultsToFastDBPython(solverCode, cgDB, fgDB):
    """Synchronize global results table to more local results table

    To account for contention with file-system databases, a multi-tier approach
    is suggested. This synchronizes results from the higher level database to
    the lower one for the purpose of successful look ups.

    Args:
        solverCode (SolverCode): Enum corresponding to simulation
        cgDB (ALDBHandle): Object to access higher level (coarse grain) database
        fgDB (ALDBHandle): Object to access lower level (fine grain) database

    Raises:
        Exception: Using Unsupported SolverCode
    """
    #TODO: Evaluate if it makes sense to also synchronize GND tables
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

def queueFGSJob(configStruct, uname, reqID, inArgs, rank, modeSwitch, cgDB, fgDB, dbCache):
    """Perform fine grain simulation

    Args:
        configStruct: Dictionary containing configuration data for simulation
        uname (str): UID of user running GLUE Code
        reqID: Monotonically increasing ID to use as job ID to look up result later
        inArgs: Arguments for fine grain simulation
        rank: Identifier of job originator. Commonly MPI rank
        modeSwitch (ALInterfaceMode): Type of fine grain simulation to run
        cgDB (ALDBHandle): Object to access higher level (coarse grain) database
        fgDB (ALDBHandle): Object to access lower level (fine grain) database
        dbCache: Container used for local cache of requests and results
    """
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
            # TODO: Evaluate if we want to insert valid analytic results to GND table
        else:
            # Call fgs with args as scheduled job
            # job will write result back
            launchedJob = False
            while(launchedJob == False):
                queueJob = getQueueUsability(uname, configStruct)
                if queueJob == True:
                    print("Processing REQ=" + str(reqID))
                    buildAndLaunchFGSJob(configStruct, rank, reqID, inArgs, modeSwitch)
                    launchedJob = True

def useAnalyticSolution(inputStruct):
    """Determine if analytic solution is sufficient

    Args:
        inputStruct: Arguments for fine grain simulation

    Returns:
        bool: Indication if analytic solution is sufficient
    """
    if isinstance(inputStruct, BGKInputs):
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
    """Compute and return analytic solution

    Args:
        inArgs: Arguments for fine grain simulation

    Raises:
        Exception: Analytic solvers not supported for this simulation type

    Returns:
        Results of analytic solution
    """
    if isinstance(inArgs, BGKInputs):
        (cond, visc, diffCoeff) = ICFAnalytical_solution(inArgs.Density, inArgs.Charges, inArgs.Temperature)
        bgkOutput = BGKOutputs(Viscosity=visc, ThermalConductivity=cond, DiffCoeff=diffCoeff)
        return bgkOutput
    else:
        raise Exception('Using Unsupported Analytic Solver')

def pollAndProcessFGSRequests(configStruct, uname):
    """General service loop of GLUE Code

    Primary function that creates a loop to run as a service to repeatedly poll databases for requests,
    process requests, and return results.

    Args:
        configStruct: Dictionary containing configuration data for simulation
        uname (str): UID of user running GLUE Code

    Raises:
        Exception: Use of unsupported SolverCode and ALInterfaceMode combination
    """
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
        #Logic to not hammer DB/learner with unnecessary retraining requests
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
    #Close Database Connection
    cgDB.closeDB()
    fgDB.closeDB()

if __name__ == "__main__":
    configStruct = processGlueCodeArguments()

    uname =  getpass.getuser()
    # We will not pass in uname via the json file

    pollAndProcessFGSRequests(configStruct, uname)
