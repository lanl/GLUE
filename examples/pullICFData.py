from alInterface import getAllGNDData
from glueCodeTypes import SolverCode
import sys
import numpy as np

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("pullICFData.py ${DB_File}")
        exit(1)
    gndData = getAllGNDData(sys.argv[1], SolverCode.BGK)
    for entry in gndData:
        print(entry)
