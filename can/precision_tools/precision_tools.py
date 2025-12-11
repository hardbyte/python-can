# -*- coding: utf-8 -*-
"""
用于本地 ScheduledExecutor 和 PrecisionSleep DLL 的 Python 封装。

该模块提供两个主要类：
1.  ScheduledExecutor: C++ 调度执行器的 Pythonic 封装，
    模仿了 Java 的 ScheduledThreadPoolExecutor 接口。
2.  PrecisionSleep: 高精度睡眠函数的封装。

注意：此模块依赖于名为 PrecisionSleep.dll 的本地 DLL。
PrecisionSleep.dll仓库开源地址：https://github.com/fshoocn/precision_tools
"""

import ctypes
import os
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Optional

"""
"""

# 为任务回调定义函数指针类型
# 第一个参数是任务ID (unsigned long long)，第二个参数是用户数据 (py_object)
TaskCallbackFunc = ctypes.CFUNCTYPE(None, ctypes.c_ulonglong, ctypes.py_object)

def _find_dll(dll_name: str = "PrecisionSleep.dll") -> Optional[Path]:
    """
    在通用编译目录或系统路径中查找 DLL。
    在相对于当前脚本的典型 CMake 构建文件夹中搜索。
    """
    # 在脚本目录和父目录中搜索
    search_paths = [Path.cwd()]
    for i in range(3):
        search_paths.append(search_paths[-1].parent)

    # 常见的编译目录名称
    build_dirs = [
        "build",
        "cmake-build-release",
        "cmake-build-debug",
        "cmake-build-release-visual-studio-amd64",
        "out/build/x64-release",
        "out/build/x64-debug",
        # 当前precision_tools.py文件所在目录
        Path(__file__).parent   
    ]

    for base_path in search_paths:
        # 检查基本路径本身
        if (base_path / dll_name).is_file():
            return base_path / dll_name
        
        # 检查通用编译目录
        for build_dir in build_dirs:
            dll_path = base_path / build_dir / dll_name
            if dll_path.is_file():
                return dll_path

    # 回退到系统范围搜索
    if sys.platform == "win32":
        try:
            # 使用系统的 DLL 搜索路径
            loader = ctypes.WinDLL(dll_name)
            return Path(loader._name)
        except (OSError, FileNotFoundError):
            pass

    return None


class ScheduledExecutor:
    """
    一个用于本地 C++ 调度线程池执行器的 Python 封装。

    该类管理本地执行器的生命周期，提供调度任务的方法，
    并确保在 Python 和 C++ 之间安全地处理回调。
    """
    _dll_path = _find_dll()
    if not _dll_path:
        raise FileNotFoundError(
            "找不到 PrecisionSleep.dll。 "
            "请确保它位于系统 PATH 或常见的生成目录中。"
        )
    
    _dll = ctypes.CDLL(str(_dll_path))

    def __init__(self, thread_pool_size: int = 4):
        """
        初始化调度执行器。
        :param thread_pool_size: 线程池中的线程数。
        """
        self._setup_function_signatures()
        
        self._executor = self._dll.ScheduledExecutor_create(thread_pool_size)
        if not self._executor:
            raise RuntimeError("创建本地调度执行器失败。")
        
        if not self._dll.ScheduledExecutor_initialize(self._executor):
            self._dll.ScheduledExecutor_destroy(self._executor)
            raise RuntimeError("初始化本地调度执行器失败。")
            
        self._active = True
        # ctypes 的返回类型不能直接在类型提示中使用，因此我们使用 'object'
        self._tasks: Dict[int, tuple] = {}
        self._task_lock = threading.Lock()

    def _setup_function_signatures(self):
        """为所有 DLL 函数设置 ctypes 的 argtypes 和 restypes。"""
        # ScheduledExecutor 函数
        self._dll.ScheduledExecutor_create.argtypes = [ctypes.c_int]
        self._dll.ScheduledExecutor_create.restype = ctypes.c_void_p
        
        self._dll.ScheduledExecutor_initialize.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_initialize.restype = ctypes.c_bool
        
        self._dll.ScheduledExecutor_shutdown.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_shutdown.restype = None
        
        self._dll.ScheduledExecutor_destroy.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_destroy.restype = None
        
        self._dll.ScheduledExecutor_isShutdown.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_isShutdown.restype = ctypes.c_bool
        
        self._dll.ScheduledExecutor_schedule.argtypes = [ctypes.c_void_p, TaskCallbackFunc, ctypes.py_object, ctypes.c_double]
        self._dll.ScheduledExecutor_schedule.restype = ctypes.c_ulonglong
        
        self._dll.ScheduledExecutor_scheduleAtFixedRate.argtypes = [ctypes.c_void_p, TaskCallbackFunc, ctypes.py_object, ctypes.c_double, ctypes.c_double]
        self._dll.ScheduledExecutor_scheduleAtFixedRate.restype = ctypes.c_ulonglong
        
        self._dll.ScheduledExecutor_cancelTask.argtypes = [ctypes.c_void_p, ctypes.c_ulonglong]
        self._dll.ScheduledExecutor_cancelTask.restype = ctypes.c_bool
        
        self._dll.ScheduledExecutor_getThreadPoolSize.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_getThreadPoolSize.restype = ctypes.c_int
        
        self._dll.ScheduledExecutor_getPendingTaskCount.argtypes = [ctypes.c_void_p]
        self._dll.ScheduledExecutor_getPendingTaskCount.restype = ctypes.c_ulonglong

    def schedule(self, task: Callable[[int, object], None], delay_ms: float, user_data=None) -> int:
        """
        调度一个一次性任务，在给定延迟后运行。
        :param task: 要执行的可调用对象。应接受两个参数: task_id (int) 和 user_data (任意对象)。
        :param delay_ms: 延迟时间（毫秒）。
        :param user_data: 可选的用户自定义数据，将传递给回调函数。
        :return: 已调度任务的 ID。
        """
        if not self._active:
            raise RuntimeError("执行器已关闭。")

        # 创建包装器，将任务ID与用户数据传递给用户回调
        def wrapper(task_id, _user_data):
            try:
                task(task_id, _user_data)
            except Exception as e:
                print(f"任务 {task_id} 执行出错: {e}")

        c_callback = TaskCallbackFunc(wrapper)
        task_id = self._dll.ScheduledExecutor_schedule(self._executor, c_callback, user_data, delay_ms)

        with self._task_lock:
            self._tasks[task_id] = (c_callback, user_data)

        return task_id

    def schedule_at_fixed_rate(self, task: Callable[[int, object], None], initial_delay_ms: float, period_ms: float, user_data=None) -> int:
        """
        调度一个周期性任务，在初始延迟后以固定周期运行。
        :param task: 要周期性执行的可调用对象。应接受两个参数: task_id (int) 和 user_data (任意对象)。
        :param initial_delay_ms: 初始延迟（毫秒）。
        :param period_ms: 周期（毫秒）。
        :param user_data: 可选的用户自定义数据，将传递给回调函数。
        :return: 已调度任务的 ID。
        """
        if not self._active:
            raise RuntimeError("执行器已关闭。")

        # 创建包装器，将任务ID与用户数据传递给用户回调
        def wrapper(task_id, _user_data):
            try:
                task(task_id, _user_data)
            except Exception as e:
                print(f"任务 {task_id} 执行出错: {e}")

        c_callback = TaskCallbackFunc(wrapper)
        task_id = self._dll.ScheduledExecutor_scheduleAtFixedRate(self._executor, c_callback, user_data, initial_delay_ms, period_ms)

        with self._task_lock:
            self._tasks[task_id] = (c_callback, user_data)

        return task_id

    def cancel_task(self, task_id: int) -> bool:
        """
        取消一个已调度的任务。
        :param task_id: 要取消的任务的 ID。
        :return: 如果任务成功取消，则为 True，否则为 False。
        """
        if not self._active:
            return False
            
        result = self._dll.ScheduledExecutor_cancelTask(self._executor, task_id)
        if result:
            with self._task_lock:
                self._tasks.pop(task_id, None)
        return result

    def get_thread_pool_size(self) -> int:
        """返回配置的线程池大小。"""
        return self._dll.ScheduledExecutor_getThreadPoolSize(self._executor)

    def get_pending_task_count(self) -> int:
        """返回待处理任务的大约数量。"""
        return self._dll.ScheduledExecutor_getPendingTaskCount(self._executor)

    def is_shutdown(self) -> bool:
        """检查执行器是否已关闭。"""
        return self._dll.ScheduledExecutor_isShutdown(self._executor)

    def shutdown(self):
        """
        关闭执行器，允许正在运行的任务完成。
        不会接受新任务。
        """
        if self._active:
            self._dll.ScheduledExecutor_shutdown(self._executor)
            self._active = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        # 本地 C++ 析构函数将被调用，它应该等待任务完成。
        # 在这里销毁句柄。
        if self._executor:
            self._dll.ScheduledExecutor_destroy(self._executor)
            self._executor = None
        with self._task_lock:
            self._tasks.clear()

    def __del__(self):
        if self._active:
            self.shutdown()
        if self._executor:
            self._dll.ScheduledExecutor_destroy(self._executor)


class PrecisionSleep:
    """
    本地 PrecisionSleep 函数的 Python 封装。
    """
    _dll_path = _find_dll()
    if not _dll_path:
        raise FileNotFoundError(
            "找不到 PrecisionSleep.dll。 "
            "请确保它位于系统 PATH 或常见的生成目录中。"
        )
    
    _dll = ctypes.CDLL(str(_dll_path))
    _initialized = False

    def __init__(self):
        """初始化 PrecisionSleep 系统。"""
        self._setup_function_signatures()
        if not PrecisionSleep._initialized:
            if not self._dll.PrecisionSleep_initialize():
                raise RuntimeError("初始化 PrecisionSleep 失败。")
            PrecisionSleep._initialized = True

    def _setup_function_signatures(self):
        """为所有 DLL 函数设置 ctypes 的 argtypes 和 restypes。"""
        self._dll.PrecisionSleep_initialize.argtypes = []
        self._dll.PrecisionSleep_initialize.restype = ctypes.c_bool
        
        self._dll.PrecisionSleep_cleanup.argtypes = []
        self._dll.PrecisionSleep_cleanup.restype = None
        
        self._dll.PrecisionSleep_sleep.argtypes = [ctypes.c_double]
        self._dll.PrecisionSleep_sleep.restype = ctypes.c_bool

    @staticmethod
    def sleep(milliseconds: float) -> bool:
        """
        以高精度睡眠指定的持续时间。
        :param milliseconds: 睡眠持续时间（毫秒）。
        :return: 成功时为 True，失败时为 False。
        """
        if not PrecisionSleep._initialized:
            raise RuntimeError("PrecisionSleep 未初始化。")
        return PrecisionSleep._dll.PrecisionSleep_sleep(milliseconds)

    @staticmethod
    def cleanup():
        """清理 PrecisionSleep 系统资源。"""
        if PrecisionSleep._initialized:
            PrecisionSleep._dll.PrecisionSleep_cleanup()
            PrecisionSleep._initialized = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()