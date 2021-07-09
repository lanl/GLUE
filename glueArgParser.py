import argparse
import json
import getpass
from glueCodeTypes import ALInterfaceMode, SolverCode, LearnerBackend, SchedulerInterface, ProvisioningInterface, DatabaseMode

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

    argParser = argparse.ArgumentParser(description='Command Line Arguments to Glue Code')

    argParser.add_argument('-i', '--inputfile', action='store', type=str, required=False, default=defaultJsonFile, help="(JSON) Input File")
    args = vars(argParser.parse_args())

    jsonFile = args['inputfile']
    configStruct = {}
    if jsonFile != "":
        with open(jsonFile) as j:
            configStruct = json.load(j)
    else:
        raise Exception('Glue Code Requires An Input Json File. python alInterface.py -i ${JSON_FILE}')

    # Convert magic numbers to enums
    if 'glueCodeMode' in configStruct:
        configStruct['glueCodeMode'] = ALInterfaceMode(configStruct['glueCodeMode'])
    if 'solverCode' in configStruct:
        configStruct['solverCode'] = SolverCode(configStruct['solverCode'])
    if 'alBackend' in configStruct:
        configStruct['alBackend'] = LearnerBackend(configStruct['alBackend'])
    if 'ProvisioningInterface' in configStruct:
        configStruct['ProvisioningInterface'] = ProvisioningInterface(configStruct['ProvisioningInterface'])
    if 'SchedulerInterface' in configStruct:
        configStruct['SchedulerInterface'] = SchedulerInterface(configStruct['SchedulerInterface'])
    configStruct['DatabaseSettings']['CoarseGraindDB']['DatabaseMode'] = \
        DatabaseMode(
            configStruct['DatabaseSettings']['CoarseGraindDB']['DatabaseMode']
        )
    configStruct['DatabaseSettings']['FineGrainDB']['DatabaseMode'] = \
        DatabaseMode(
            configStruct['DatabaseSettings']['FineGrainDB']['DatabaseMode']
        )

    return configStruct
