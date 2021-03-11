from glueCodeTypes import BGKInputs
from alInterface import getAnalyticSolution
import sys


def runAndPrintData(nRanks, nReqs):
    resultsTable = []
    # Generate inputs and get analytic solutions
    for r in range(nRanks):
        for i in range(nReqs):
            temp = 160 + 0.05 * i * (r + 1)
            dens = 4.44819405e+24
            chargeA = 0.9308375079943152
            chargeB = 11.544522277358098
            inArgs = BGKInputs(Temperature=temp,
                               Density=[dens, dens, 0.0, 0.0],
                               Charges=[chargeA, chargeB, 0.0, 0.0]
                               )
            outArgs = getAnalyticSolution(inArgs)
            resultsTable.append((inArgs, outArgs))
    # Print results to file (terminal) in way we can diff later
    for r in range(nRanks):
        for i in range(nReqs):
            index = (r * nReqs) + i
            print("[" + str(r) + "," + str(i) + "] : "
                  + str(resultsTable[index][0])
                  + " -> "
                  + str(resultsTable[index][1])
                  )


if __name__ == "__main__":
    nRanks = 1
    nReqs = 2048
    if len(sys.argv) == 3:
        nRanks = int(sys.argv[1])
        nReqs = int(sys.argv[2])
    runAndPrintData(nRanks, nReqs)

