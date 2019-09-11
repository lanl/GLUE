import argparse
from alInterface import BGKOutputs, BGKInputs, buildAndLaunchLAMMPSJob
from slurmInterface import getSlurmQueue

def runLammpsQueue(numReqs, maxJobs, tag, dbPath, uname, lammps):
    # Generate requests
    lammpsIns = []
    for i in range(numReqs):
        inValues = BGKInputs(Temperature=500000.0, Density=[0.0]*4, Charges=[0.0]*4)
        for j in range(4):
            inValues.Charges[j] = 0.0 + 0.15*i + 0.07*j
            inValues.Density[j] = 0.0 + 0.15*j + 0.07*i
        lammpsIns.append(inValues)
    # Fire off requests to slurm
    for reqId in range(numReqs):
        launchedJob = False
        while(launchedJob == False):
            queueState = getSlurmQueue(uname)
            if queueState[0] < maxJobs:
                buildAndLaunchLAMMPSJob(0, tag, dbPath, uname, lammps, reqId, lammpsIns[reqId])
                launchedJob = True
    return

if __name__ == "__main__":
    defaultFName = "testDB.db"
    defaultTag = "DUMMY_TAG_42"
    defaultLammps = "./lmp"
    defaultUname = "tcg"
    defaultMaxJobs = 4
    defaultNumJobs = 8

    argParser = argparse.ArgumentParser(description='Test Driver To Ensure Slurm Behavior')

    argParser.add_argument('-t', '--tag', action='store', type=str, required=False, default=defaultTag, help="Tag for DB Entries")
    argParser.add_argument('-l', '--lammps', action='store', type=str, required=False, default=defaultLammps, help="Path to LAMMPS Binary")
    argParser.add_argument('-d', '--db', action='store', type=str, required=False, default=defaultFName, help="Filename for sqlite DB")
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")
    argParser.add_argument('-n', '--numjobs', action='store', type=int,  required=False, default=defaultNumJobs, help="Number of Lammps Tasks")

    args = vars(argParser.parse_args())

    tag = args['tag']
    fName = args['db']
    lammps = args['lammps']
    uname = args['uname']
    jobs = args['maxjobs']
    reqs = args['numjobs']

    runLammpsQueue(reqs, jobs, tag, fName, uname, lammps)
