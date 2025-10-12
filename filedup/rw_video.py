import os
import io
import base64
import filedup.rw_interface as rw_interface

# 常见视频文件扩展名
FILE_TYPES = ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'mpg', 'mpeg', '3gp', 'm4v', 'vob', 'ogv']

class RWVideo(rw_interface.RWInterface):
    """
    处理各种视频文件的读取接口类。
    注意：此类仅实现读取功能，不实现完整的写入功能。
    """
    def __init__(self):
        super().__init__()
        self.name = 'RWVideo'
        self.description = '处理各种视频文件的读取接口类。'
    
    @staticmethod
    def register_extension():
        """
        注册该接口类处理的文件扩展名。
        """
        return {'ext': FILE_TYPES, 'handler': RWVideo()}
    
    def unregister_extension(self):
        """
        注销该接口类处理的文件扩展名。
        """
        return {'ext': FILE_TYPES, 'handler': None}
    
    @staticmethod
    def get_extensions() -> list:
        """
        获取该接口类处理的文件扩展名列表。
        """
        return FILE_TYPES
    
    def can_handle(self, filename: str) -> bool:
        """
        判断该接口类是否能够处理指定的文件扩展名。
        """
        if not filename:
            return False
        
        # 获取文件扩展名（转为小写）
        try:
            file_extension = filename.split('.')[-1].lower()
            return file_extension in FILE_TYPES
        except:
            return False
    
    def open(self, filename: str, mode: str = 'r'):
        """
        打开视频文件。
        """
        if not os.path.exists(filename):
            return None
        
        try:
            # 以二进制模式打开文件
            file_object = open(filename, 'rb')
            return file_object
        except Exception as e:
            print(f"无法打开文件 {filename}: {str(e)}")
            return None
    
    def close(self, file_object, save: bool = True):
        """
        关闭视频文件。
        """
        if file_object is not None:
            try:
                file_object.close()
            except:
                pass
        return True
    
    def read(self, file_object):
        """
        读取视频文件的内容。
        由于我们现在使用外部播放器播放视频，不需要读取整个文件内容。
        """
        if file_object is None:
            return None
        
        try:
            # 获取文件大小信息而不是读取全部内容
            # 保存当前位置
            current_pos = file_object.tell()
            # 移动到文件开头
            file_object.seek(0, 2)  # 移动到文件末尾
            file_size = file_object.tell()
            # 恢复文件位置
            file_object.seek(current_pos)
            # 返回文件大小信息
            return f"FILE_SIZE:{file_size}"
        except Exception as e:
            print(f"读取文件信息失败: {str(e)}")
            return None
    
    def write(self, file_object, data: any = None):
        """
        写入视频文件的内容。
        注意：根据要求，此类不实现完整的写入功能。
        """
        # 按照要求，不实现完整的write功能
        print("警告：RWVideo类不支持写入功能。")
        return None
    
    def handle_file(self, filename: str, mode: str, data: any = None):
        """
        处理视频文件。
        由于我们使用外部播放器播放视频，不再需要Base64编码视频内容。
        """
        if mode == 'r':
            # 读取模式 - 只需确认是视频文件并返回文件信息
            try:
                # 检查文件是否存在
                if not os.path.exists(filename):
                    return None, None
                
                # 获取文件大小
                file_size = os.path.getsize(filename)
                
                # 对于大型视频文件，直接返回文件大小信息
                # 由于我们使用外部播放器，不再需要读取和编码视频内容
                return 'video', f"FILE_SIZE:{file_size}"
            except Exception as e:
                print(f"处理视频文件时出错: {str(e)}")
                return None, None
        elif mode == 'w':
            # 写入模式 - 不支持
            print(f"警告：RWVideo类不支持写入模式。")
            return None, None
        
        return None, None