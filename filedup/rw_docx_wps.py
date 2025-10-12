import os
import win32com.client
import filedup.rw_interface as rw_interface

FILE_TYPES=['doc','docx','wps']

class RWDocxWps(rw_interface.RWInterface):
    """
    处理 docx 和 wps 文件的读写接口类。
    """
    def __init__(self):
        super().__init__()
        self.word_app = None
        self.name = 'RWDocxWps'
        self.description = '处理 docx 和 wps 文件的读写接口类。'
    
    @staticmethod
    def register_extension():
        """
        注册该接口类处理的文件扩展名。
        """    
        return {'ext': FILE_TYPES, 'handler': RWDocxWps()}
    
    def unregister_extension(self):
        """
        注销该接口类处理的文件扩展名。
        return {'ext': FILE_TYPES, 'handler': None}
        """
        if self.word_app is not None:
            self.word_app.Quit()
            self.word_app = None
        return {'ext': FILE_TYPES, 'handler': None}


    @staticmethod
    def get_extensions() -> list:
        """
        return FILE_TYPES: 该接口类处理的文件扩展名列表。
        获取该接口类处理的文件扩展名列表。
        """
        return FILE_TYPES

    def can_handle(self, filename: str) -> bool:
        """
        判断该接口类是否能够处理指定的文件扩展名。
        return False: 该接口类无法处理该扩展名的文件。
        return True: 该接口类可以处理该扩展名的文件。
        """
        file_extension = filename.split('.')[-1]
        return file_extension in FILE_TYPES
               
    def open(self, filename: str, mode: str = 'r'):
        """
        打开 doc、docx 和 wps 文件。
        param filename: 文件路径。
        param mode: 文件打开模式，'r' 表示只读，'w' 表示写入。
        return None: 文件不存在或无法打开。
        return file object: 文件对象。
        """
        if not os.path.exists(filename):
            return None
        try:
            if self.word_app is None:
                self.word_app = win32com.client.Dispatch('Word.Application')
            if 'w' in mode:
                file_object = self.word_app.Documents.Add()
                file_object.SaveAs(filename)
            elif 'r' in mode:
                file_object = self.word_app.Documents.Open(filename)
            else:
                return None
        except Exception as e:
            print(e)
            return None
        return file_object
    
    def close(self, file_object,save:bool = True):
        """
        关闭 docx 和 wps 文件。
        return None: 文件对象不存在或无法关闭。
        return True: 文件对象关闭成功。
        """
        if file_object is not None:
            if save:
                file_object.Save()
            file_object.Close()
        return True
    
    def read(self, file_object):
        """
        读取 docx 和 wps 文件的内容。
        return None: 文件对象不存在或无法读取。
        return str: 文件内容。
        """
        if file_object is None:
            return None
        data = file_object.Content.Text
        return data
    
    def write(self, file_object, data:any = None):
        """
        写入 docx 和 wps 文件的内容。
        return None: 文件对象不存在或无法写入。
        return True: 文件内容写入成功。 
        """
        if file_object is None:
            return None

        file_object.Content.Text = data
        return True

    def save(self, file_object, data:any = None):
        """
        保存 docx 和 wps 文件的内容。
        return None: 文件对象不存在或无法保存。
        return True: 文件内容保存成功。
        """
        if file_object is None:
            return None
        file_object.Save()
        return True

    def handle_file(self, filename: str, mode: str, data: any = None):
        """
        处理 docx 和 wps 文件。
        filename: 文件路径。
        mode: 文件打开模式，'r'为读取，'w'为写入。
        data: 写入文件的内容，仅在mode为'w'时有效。
        return False: 处理失败。
        return True: 处理成功。
        """
        
        if 'w' in mode:
            file_object = self.open(filename, mode)
            if file_object is None:
                return None, None
            self.write(file_object, data)
            self.save(file_object)
            self.close(file_object)
            return ('text',data)
        elif 'r' in mode:
            file_object = self.open(filename, mode)
            if file_object is None:
                return None, None
            data = self.read(file_object)
            self.close(file_object)
            return ('text',data)
        else:
            return None, None


