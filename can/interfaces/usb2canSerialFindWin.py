try:
    import win32com.client
except ImportError:
    print("win32com client module required")


def WMIDateStringToDate(dtmDate):
    if (dtmDate[4] == 0):
        strDateTime = dtmDate[5] + '/'
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + '/'

    if (dtmDate[6] == 0):
        strDateTime = strDateTime + dtmDate[7] + '/'
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + '/'
        strDateTime = strDateTime + dtmDate[0] + dtmDate[1] + dtmDate[2] + dtmDate[3] + " " + dtmDate[8] + dtmDate[
            9] + ":" + dtmDate[10] + dtmDate[11] + ':' + dtmDate[12] + dtmDate[13]
    return strDateTime


strComputer = "."
objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
objSWbemServices = objWMIService.ConnectServer(strComputer, "root\cimv2")
colItems = objSWbemServices.ExecQuery("SELECT * FROM Win32_USBControllerDevice")


def serial():
    for objItem in colItems:
        string = objItem.Dependent
        # find based on beginning of serial
        if "ED" in string:
            # print "Dependent:" + ` objItem.Dependent`
            string = string[len(string) - 9:len(string) - 1]

            return string
