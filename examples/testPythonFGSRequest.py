from glueCodeTypes import BGKInputs
from submitFGSJob import submitFGSJobs
import os
import numpy as np

if __name__ == "__main__":
    # Really convoluted way to get some example inputs
    pythonScriptDir = os.path.dirname(os.path.realpath(__file__))
    repoDir = os.path.dirname(pythonScriptDir)
    trainingDir = os.path.join(repoDir, "training")
    csv = os.path.join(trainingDir, "bgk.csv")
    trainingEntries = np.loadtxt(csv)
    testList = []
    for row in trainingEntries[:20]:
        testList.append(BGKInputs(Temperature=row[0], Density=[row[1], row[2], 0.0, 0.0], Charges=[row[3], row[4], 0.0, 0.0]))
    # Now submit them
    submitFGSJobs(testList, "testDB.db", "DUMMY_TAG_42", -1)
