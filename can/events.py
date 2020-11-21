WAIT_OBJECT_0 = 0x00000000
INFINITE = -1

try:
    import ctypes.wintypes
    import ctypes

    _HANDLE = ctypes.wintypes.HANDLE
    _BOOL = ctypes.wintypes.BOOL
    _LARGE_INTEGER = ctypes.wintypes.LARGE_INTEGER
    _LONG = ctypes.wintypes.LONG
    _DWORD = ctypes.wintypes.DWORD

    _kernel32 = ctypes.windll.Kernel32

    _CreateWaitableTimerW = _kernel32.CreateWaitableTimerW
    _CreateWaitableTimerW.restype = _HANDLE

    def CreateWaitableTimer(lpTimerAttributes, bManualReset, lpTimerName):
        return _CreateWaitableTimerW(
            lpTimerAttributes,
            _BOOL(bManualReset),
            lpTimerName
        )


    _CancelWaitableTimer = _kernel32.CancelWaitableTimer
    _CancelWaitableTimer.restype = _BOOL

    def CancelWaitableTimer(hTimer):
        return _CancelWaitableTimer(_HANDLE(hTimer))

    _SetWaitableTimer = _kernel32.SetWaitableTimer
    _SetWaitableTimer.restype = _BOOL

    def SetWaitableTimer(
        hTimer,
        lpDueTime,
        lPeriod,
        pfnCompletionRoutine,
        lpArgToCompletionRoutine,
        fResume
    ):
        lpDueTime = _LARGE_INTEGER(lpDueTime)
        return _SetWaitableTimer(
            _HANDLE(hTimer),
            ctypes.byref(lpDueTime),
            _LONG(lPeriod),
            pfnCompletionRoutine,
            lpArgToCompletionRoutine,
            _BOOL(fResume)
        )

    _WaitForSingleObject = _kernel32.WaitForSingleObject
    _WaitForSingleObject.restype = _DWORD

    def WaitForSingleObject(hHandle, dwMilliseconds, _=None):
        return _WaitForSingleObject(
            _HANDLE(hHandle),
            _DWORD(dwMilliseconds)
        )

    _CreateEventW = _kernel32.CreateEventW
    _CreateEventW.restype = _HANDLE

    def CreateEvent(lpEventAttributes, bManualReset, bInitialState, lpName):
        return _CreateEventW(
            lpEventAttributes,
            _BOOL(bManualReset),
            _BOOL(bInitialState),
            lpName
        )

except ImportError:
    import time

    def CreateWaitableTimer(*_):
        return None

    def CancelWaitableTimer(_):
        return True

    def SetWaitableTimer(*_):
        return True

    def WaitForSingleObject(_, dwMilliseconds, dwStarted):
        # Compensate for the time it takes to send the message
        delay = (dwMilliseconds / 1000.0) - (time.perf_counter() - dwStarted)
        time.sleep(max(0.0, delay))

    def CreateEvent(*_):
        return None

