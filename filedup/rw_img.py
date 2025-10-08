import os
import io
import base64
from PIL import Image
import rw_interface

FILE_TYPES = ['bmp', 'jpg', 'jpeg', 'png', 'gif', 'tiff', 'webp', 'ppm', 'pgm', 'pbm', 'pnm', 'svg']

class RWImg(rw_interface.RWInterface):
    """
    处理各种图片文件的读写接口类。
    """
    def __init__(self):
        super().__init__()
        self.name = 'RWImg'
        self.description = '处理各种图片文件的读写接口类。'
    
    @staticmethod
    def register_extension():
        """
        注册该接口类处理的文件扩展名。
        """
        return {'ext': FILE_TYPES, 'handler': RWImg()}
    
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
        打开图片文件。
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
        关闭图片文件。
        """
        if file_object is not None:
            try:
                file_object.close()
            except:
                pass
        return True
    
    def read(self, file_object):
        """
        读取图片文件的内容。
        """
        if file_object is None:
            return None
        
        try:
            # 保存当前位置
            current_pos = file_object.tell()
            # 移动到文件开头
            file_object.seek(0)
            # 读取所有内容
            content = file_object.read()
            # 恢复文件位置
            file_object.seek(current_pos)
            return content
        except Exception as e:
            print(f"读取文件内容失败: {str(e)}")
            return None
    
    def write(self, file_object, data: any = None):
        """
        写入图片文件的内容。
        """
        if file_object is None or data is None:
            return None
        
        try:
            # 将文件指针移到开头
            file_object.seek(0)
            # 写入数据
            file_object.write(data)
            # 截断文件（以防新内容比旧内容短）
            file_object.truncate()
            return True
        except Exception as e:
            print(f"写入文件内容失败: {str(e)}")
            return None
    
    def handle_file(self, filename: str, mode: str, data: any = None):
        """
        处理图片文件。
        """
        if mode == 'r':
            # 读取模式
            file_object = self.open(filename, mode)
            if file_object is None:
                return None, None
            
            try:
                # 读取图片内容
                content = self.read(file_object)
                
                # 尝试使用PIL打开图片进行验证
                try:
                    # 使用BytesIO创建一个内存中的文件对象
                    img = Image.open(io.BytesIO(content))
                    img.verify()  # 验证图片文件的有效性
                except Exception as e:
                    print(f"不是有效的图片文件 {filename}: {str(e)}")
                    self.close(file_object)
                    return None, None
                
                # 如果是SVG文件，直接返回
                if filename.lower().endswith('.svg'):
                    # SVG是文本格式，需要解码
                    try:
                        svg_content = content.decode('utf-8')
                        return 'img', svg_content
                    except:
                        pass
                
                # 对于其他图片格式，返回base64编码的内容
                base64_content = base64.b64encode(content).decode('utf-8')
                return 'img', base64_content
            finally:
                # 确保文件被关闭
                self.close(file_object)
        elif mode == 'w':
            # 写入模式
            if data is None:
                return None, None
            
            file_object = self.open(filename, mode)
            if file_object is None:
                return None, None
            
            try:
                # 如果数据是base64编码的，先解码
                if isinstance(data, str) and data.startswith('data:image/'):
                    # 提取base64数据
                    try:
                        base64_data = data.split(',')[1]
                        binary_data = base64.b64decode(base64_data)
                        result = self.write(file_object, binary_data)
                    except:
                        result = self.write(file_object, data.encode('utf-8'))
                elif isinstance(data, str):
                    # 如果是字符串，编码后写入
                    result = self.write(file_object, data.encode('utf-8'))
                else:
                    # 直接写入二进制数据
                    result = self.write(file_object, data)
                
                return 'img', result if result else None
            finally:
                # 确保文件被关闭
                self.close(file_object)
        
        return None, None