from glueCodeTypes import ALInterfaceMode, SolverCode, BGKInputs, BGKOutputs
import sqlite3

def getSQLFromReq(fgsInput, tag, reqNum):
    if isinstance(fgsInput, BGKInputs):
        insStr = "INSERT INTO BGKREQS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        insArgs = (tag, -1, reqNum,
                   fgsInput.Temperature,
                   fgsInput.Density[0],
                   fgsInput.Density[1],
                   fgsInput.Density[2],
                   fgsInput.Density[3],
                   fgsInput.Charges[0],
                   fgsInput.Charges[1],
                   fgsInput.Charges[2],
                   fgsInput.Charges[3],
                   ALInterfaceMode.FGS)
        return (insStr, insArgs)
    else:
        raise Exception("Invalid input passed to getSQLFromReq() in submitFGSJob.py")

def getPersistentReqNumber():
    # Kludge to get a c-style static int
    try:
        getPersistentReqNumber.counter += 1
    except:
        getPersistentReqNumber.counter = 0
    return getPersistentReqNumber.counter

def submitFGSJobs(inputList, sqlDBPath, tag):
    # Then fire off every request
    for req in inputList:
        # Generate SQL insert string and tuple
        (insString, insArgs) = getSQLFromReq(req, tag, getPersistentReqNumber())
        sqlDB = sqlite3.connect(dbPath)
        sqlCursor = sqlDB.cursor()
        sqlCursor.execute(insString, insArgs)
        sqlDB.commit()
        sqlCursor.close()
        sqlDB.close()

if __name__ == "__main__":
    raise Exception("submitFGSJob.py currently does not support standalone use")
