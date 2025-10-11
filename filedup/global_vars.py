
REGISTERED_HANDLERS_FILENAME="reg_handlers.json"
FILE_FEATURES_DB_FILENAME="_file_features.db"
FILE_DUMP_FILENAME="_file_dump.json"


LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARN=2

LOG_LEVEL=LOG_LEVEL_INFO

def log_print(*args, **kwargs):
    """打印日志"""
    if LOG_LEVEL>=LOG_LEVEL_INFO:
        print(*args, **kwargs)
        
#目前版本号
#更新时间：2025-10-10
VERSION="0.1.0"
