def getSQLArrGenString(fName, dType, length):
    tString = ""
    if dType == int:
        tString = "INT"
    elif dType == float:
        tString = "REAL"
    else:
        raise Exception('Requested Incompatible SQL Trype')
    retStr = ""
    for i in range(length):
        retStr += fName + "_" + str(i) + " " + tString + ", "
    return retStr
