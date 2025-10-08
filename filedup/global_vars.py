
REGISTERED_HANDLERS_FILENAME="reg_handlers.json"
FILE_FEATURES_DB_FILENAME="file_features.db"


LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARN=2

LOG_LEVEL=LOG_LEVEL_WARN

def log_print(*args, **kwargs):
    """打印日志"""
    if LOG_LEVEL<=LOG_LEVEL_INFO:
        print(*args, **kwargs)