import argparse
import json
import getpass
from glueCodeTypes import ALInterfaceMode, SolverCode, LearnerBackend, SchedulerInterface, ProvisioningInterface

def processGlueCodeArguments():
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultLammps = ""
    defaultUname = getpass.getuser()
    defaultSqlite = "sqlite3"
    defaultSbatch = "/usr/bin/sbatch"
    defaultMaxJobs = 4
    defaultProcessing = ALInterfaceMode.FGS
    defaultRanks = 1
    defaultSolver = SolverCode.BGK
    defaultALBackend = LearnerBackend.FAKE
    defaultGNDThresh = 5
    defaultJsonFile = ""
    defaultGenOrRead = 0
    defaultScheduler = SchedulerInterface.SLURM

    argParser = argparse.ArgumentParser(description='Command Line Arguments to Glue Code')

    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-c', '--code', action='store', type=int, required=False, default=defaultSolver, help="Code to expect Packets from (BGK=0)")
    argParser.add_argument('-i', '--inputfile', action='store', type=str, required=False, default=defaultJsonFile, help="(JSON) Input File")
    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-q', '--sqlite', action='store', type=str, required=False, default=defaultSqlite, help="Path to sqlite3 Binary")
    argParser.add_argument('-s', '--sbatch', action='store', type=str, required=False, default=defaultSbatch, help="Path to sbatch Binary")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")
    argParser.add_argument('-m', '--mode', action='store', type=int, required=False, default=defaultProcessing, help="Default Request Type (FGS=0)")
    argParser.add_argument('-r', '--ranks', action='store', type=int, required=False, default=defaultRanks, help="Number of MPI Ranks to Listen For")
    argParser.add_argument('-a', '--albackend', action='store', type=int, required=False, default=defaultALBackend, help='(Active) Learning Backend to Use')
    argParser.add_argument('-g', '--retrainthreshold', action='store', type=int, required=False, default=defaultGNDThresh, help='Number of New GND Results to Trigger an AL Retrain')
    argParser.add_argument('-y', '--genorread', action='store', type=int, required=False, default=defaultGenOrRead, help="Generate or Read Training Data")

    args = vars(argParser.parse_args())

    jsonFile = args['inputfile']
    configStruct = {}
    if jsonFile != "":
        with open(jsonFile) as j:
            configStruct = json.load(j)

    tag = args['tag']
    if not 'tag' in configStruct:
        configStruct['tag'] = tag
    fName = args['db']
    if not 'dbFileName' in configStruct:
        configStruct['dbFileName'] = fName
    sqlite = args['sqlite']
    if not 'SQLitePath' in configStruct:
        configStruct['SQLitePath'] = sqlite
    sbatch = args['sbatch']
    ranks = args['ranks']
    if not 'ExpectedMPIRanks' in configStruct:
        configStruct['ExpectedMPIRanks'] = ranks
    mode = ALInterfaceMode(args['mode'])
    if not 'glueCodeMode' in configStruct:
        configStruct['glueCodeMode'] = mode
    else:
        configStruct['glueCodeMode'] = ALInterfaceMode(configStruct['glueCodeMode'])
    code = SolverCode(args['code'])
    if not 'solverCode' in configStruct:
        configStruct['solverCode'] = code
    else:
        configStruct['solverCode'] = SolverCode(configStruct['solverCode'])
    alBackend = LearnerBackend(args['albackend'])
    if not 'alBackend' in configStruct:
        configStruct['alBackend'] = alBackend
    else:
        configStruct['alBackend'] = LearnerBackend(configStruct['alBackend'])
    if not 'ActiveLearningVariables' in configStruct:
        configStruct['ActiveLearningVariables'] = {'GNDthreshold':args['retrainthreshold'], 'NumberOfRequestingActiveLearners':1}
    if(configStruct['ActiveLearningVariables']['GNDthreshold'] < 0):
        configStruct['ActiveLearningVariables']['GNDthreshold'] = sys.maxsize
    if not 'SpackVariables' in configStruct:
        configStruct['SpackVariables'] = {'SpackCompilerAndMPI':"%gcc@7.3.0 ^openmpi@3.1.3%gcc@7.3.0", "SpackLAMMPS":"lammps+mpi~ffmpeg"}
    genOrRead = args['genorread']
    if not 'GenerateTrainingData' in configStruct:
        if(genOrRead == 0):
            configStruct['GenerateTrainingData'] = True
        else:
            configStruct['GenerateTrainingData'] = False
    if not 'ReadTrainingData' in configStruct:
        if(genOrRead == 1):
            configStruct['ReadTrainingData'] = True
        else:
            configStruct['ReadTrainingData'] = False
    if not 'ProvisioningInterface' in configStruct:
        configStruct['ProvisioningInterface'] = ProvisioningInterface.SPACK
    else:
        configStruct['ProvisioningInterface'] = ProvisioningInterface(configStruct['ProvisioningInterface'])
    if not 'SchedulerInterface' in configStruct:
        configStruct['SchedulerInterface'] = SchedulerInterface.SLURM
    else:
        configStruct['SchedulerInterface'] = SchedulerInterface(configStruct['SchedulerInterface'])
    if configStruct['SchedulerInterface'] == SchedulerInterface.SLURM:
        if not 'SlurmScheduler' in configStruct:
            configStruct['SlurmScheduler'] = {"ThreadsPerMPIRankForSlurm":1, "NodesPerSlurmJob":1, "MaxSlurmJobs":4, "SlurmPartition":"general","SBatchPath":sbatch}
    if configStruct['SchedulerInterface'] == SchedulerInterface.BLOCKING:
        if not 'BlockingScheduler' in configStruct:
            configStruct['BlockingScheduler'] = {"MPIRanksForBlockingRuns":4}
    if configStruct['SchedulerInterface'] == SchedulerInterface.FLUX:
        if not 'FluxScheduler' in configStruct:
            configStruct['FluxScheduler'] = {"SlotsPerJobForFlux":1, "CoresPerSlotForFlux":1, "NodesPerJobForFlux":1, "ConcurrentJobs": 24}
    if code == SolverCode.BGK and not 'ICFParameters' in configStruct:
        configStruct['ICFParameters'] =  {"RelativeError":0.0001}

    return configStruct
