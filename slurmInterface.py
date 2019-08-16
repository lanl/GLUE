import argparse
import subprocess
import typing
import sys

def checkSlurmQueue(uname: str):
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

def launchSlurmJob(script: str):
    try:
        runproc = subprocess.run(
            ["sbatch", uname],
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



def getSlurmQueue(uname: str):
    slurmOut = checkSlurmQueue(uname)
    if slurmOut == "":
        return (sys.maxsize, [])
    strList = slurmOut.splitlines()
    if len(strList) > 1:
        return (len(strList) - 1, strList[1:])
    else:
        return (0, [])


if __name__ == "__main__":
    defaultUname = "tcg"
    defaultMaxJobs = 4

    argParser = argparse.ArgumentParser(description='Python Interface to Slurm')
    argParser.add_argument('-u', '--uname', action='store', type=str, required=False, default=defaultUname, help="Username to Query Slurm With")
    argParser.add_argument('-j', '--maxjobs', action='store', type=int, required=False, default=defaultMaxJobs, help="Maximum Number of Slurm Jobs To Enqueue")

    args = vars(argParser.parse_args())
    uname = args['uname']
    jobs = args['maxjobs']

    squeue = getSlurmQueue(uname)
    if(squeue[0] != -1):
        if(squeue[0] > jobs):
            print(str(squeue[0]) + " > " +  str(jobs))
        for line in squeue[1]:
            print(line)
    else:
        print(squeue[0])
