from enum import Enum
import sqlite3 as lite

class FineGrainProvider(Enum):
    LAMMPS = 0
    MYSTIC = 1
    FAKE = 2

# TODO: Probably make mode an enum
def pollAndProcessFGSRequests(rankArr, mode):
    reqNumArr = [0] * len(rankArr)

    # TODO: Figure out a way to stop that isn't ```kill - 9```
    while True:
        for i in range(0, len(rankArr)):
            rank = rankArr[i]
            req = reqNumArr[i]
            # TODO: Again, asynchrony and parallelism are goals
            reqName = "fgsReq_" + str(rank) + "_" + str(req)
            try:
                reqFid = open(reqName, 'r')
                fline = reqFid.readline()
                reqFid.close()
                result = -4.4
                # TODO: process fline
                # Pass req arguments to fine grain solver
                if mode == FineGrainProvider.LAMMPS:
                    # call lammps with args
                    result = 0.0
                elif mode == FineGrainProvider.MYSTIC:
                    # call mystic, that might call lammps, with args
                    result = 1.1
                elif mode == FineGrainProvider.FAKE:
                    # Do nothing? Or find a reasonable analytic solution
                    result = 2.2
                # Now write the result
                ackName = "fgsAck_" + str(rank) + "_" + str(req)
                ackFid = open(ackName, 'w')
                ackFid.write(str(result) + "\n")
                ackFid.close()
                #Increment request number
                reqNumArr[i] = reqNumArr[i] + 1
            except:
                pass


if __name__ == "__main__":
    pollAndProcessFGSRequests([0, 1], FineGrainProvider.FAKE)