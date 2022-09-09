def getSQLArrGenString(fName, dType, length):
    """Generate SQL string for array arguments

    Args:
        fName (str): Field name
        dType : Data type of field
        length (int): Number of elements in array

    Raises:
        Exception: Passed in incompatible dType

    Returns:
        str: List of fields, with type, to pass to SQL query
    """
    tString = ""
    if dType == int:
        tString = "INT"
    elif dType == float:
        tString = "REAL"
    else:
        raise Exception('Requested Incompatible SQL Type')
    retStr = ""
    for i in range(length):
        retStr += fName + "_" + str(i) + " " + tString + ", "
    return retStr
