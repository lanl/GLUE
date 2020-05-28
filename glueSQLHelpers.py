def getSQLArrGenString(fName, dType, length):
    tString = ""
    if dType == int:
        tString = "int"
    elif dType == float:
        tString = "real"
    else:
        raise Exception('Requested Incompatible SQL Trype')
    retStr = ""
    for i in range(length):
        retStr += fName + "_" + str(i) + " " + tString + " ,"
    return retStr
