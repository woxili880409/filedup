
import os
import sys

# 处理PyInstaller打包环境
if hasattr(sys, '_MEIPASS'):
    # 在打包环境中，获取可执行文件所在目录
    BASE_DIR = sys._MEIPASS
else:
    # 在开发环境中，使用脚本所在目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 使用绝对路径引用文件
REGISTERED_HANDLERS_FILENAME = os.path.join(BASE_DIR, "reg_handlers.json")
FILE_FEATURES_DB_FILENAME = "_file_features.db"  # 这个文件应该在运行目录中创建
FILE_DUMP_FILENAME = "_file_dump.json"  # 这个文件应该在运行目录中创建

LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARN=2
LOG_LEVEL_ERROR=3

LOG_LEVEL=LOG_LEVEL_INFO

def set_log_level(log_level):
    """设置日志级别"""
    global LOG_LEVEL
    LOG_LEVEL=log_level

def log_print(*args,log_level=LOG_LEVEL_INFO):
    """打印日志"""
    if log_level>=LOG_LEVEL:
        print(*args)

def norm_exists_path(path,skip_link=True):
    """归一化路径"""
    if not os.path.exists(path):
        return None
    if skip_link and os.path.islink(path):
        return None
    else:
        path=os.path.realpath(os.path.abspath(path))
    return os.path.normpath(path)
        
#目前版本号
#更新时间：2025-10-10
VERSION="0.1.0"
