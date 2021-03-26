from glueCodeTypes import BGKInputs
from alInterface import getAnalyticSolution
import numpy as np
import sys


def runAndPrintData(nRanks, nReqs):
    resultsTable = []
    # Generate inputs and get analytic solutions
    for r in range(nRanks):
        for i in range(nReqs):
            temp = 160 + 10 * i * (r + 1)
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
    outputList = []
    for r in range(nRanks):
        for i in range(nReqs):
            index = (r * nReqs) + i
            # Convert to numpy array
            resultRow = [r, i]
            resultRow.append(resultsTable[index][0].Temperature)
            for j in range(4):
                resultRow.append(resultsTable[index][0].Density[j])
            for j in range(4):
                resultRow.append(resultsTable[index][0].Charges[j])
            resultRow.append(resultsTable[index][1].Viscosity)
            resultRow.append(resultsTable[index][1].ThermalConductivity)
            for j in range(10):
                resultRow.append(resultsTable[index][1].DiffCoeff[j])
            outputList.append(resultRow)
    outputArr = np.array(outputList)
    outName = str(nRanks) + "_" + str(nReqs) + "_py.dat"
    np.savetxt(outName, outputArr)

if __name__ == "__main__":
    nRanks = 1
    nReqs = 2048
    if len(sys.argv) == 3:
        nRanks = int(sys.argv[1])
        nReqs = int(sys.argv[2])
    runAndPrintData(nRanks, nReqs)

