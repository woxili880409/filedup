import os
import json
import filedup.rw_interface
from filedup.global_vars import REGISTERED_HANDLERS_FILENAME, log_print, FILE_FEATURES_DB_FILENAME

class RWRegHandlers:
    """注册文件处理器"""
    def __init__(self):
        self.register_handlers=[]
        self.register_file_handler()
                
    def register_file_handler(self):
        """注册文件处理函数"""
        reg_file=json.load(open(REGISTERED_HANDLERS_FILENAME,"r"))
        for handler in reg_file["regs"]:
            self.register_file_handler_by_json(handler)
            
    def register_file_handler_by_json(self,handler_json):
        """注册文件处理函数"""
        #根据json文件中的key:value，导入key模块，并注册文件处理器
        if not handler_json["enabled"]:
            # print(f"文件处理器 {handler_json['ext']} 已禁用，不注册")
            return
        # 正确导入子模块，使用fromlist参数确保导入的是子模块而不是包
        handler_module = __import__(handler_json["module"], fromlist=[''])
        # 移除错误的__path__设置
        handler_class:filedup.rw_interface.RWInterface = getattr(handler_module, handler_json["class"])
        reged=handler_class.register_extension()
        
        existing_handler = next((x for x in self.register_handlers if x["ext"] == reged["ext"]), None)
        if existing_handler:
            log_print(f"文件处理器 {reged['ext']} 已存在，不重复注册")
            return        
        self.register_handlers.append({"ext":reged["ext"],"handler":reged["handler"]})
        print(f"注册文件处理器: {handler_json['ext']}")

    def unregister_file_handler(self):
        """注销文件处理函数"""
        if not self.register_handlers:
            return
        for h in self.register_handlers:
            print(f"注销文件处理器: {h['ext']}")
            h["handler"].unregister_extension()
            # self.register_handlers.remove(h)
        self.register_handlers.clear()
        
    def default_file_handler(self, file_path, max_lines=100):
        """读取文件内容"""       
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = []
                for i, line in enumerate(file):
                    if i >= max_lines:
                        lines.append("... 内容过长，已截断 ...")
                        break
                    lines.append(line.rstrip('\n\r'))
                return 'text', '\n'.join(lines)
        except UnicodeDecodeError:
            # 尝试使用二进制模式读取文本文件
            try:
                with open(file_path, 'rb') as file:
                    content = file.read(4096)  # 只读取前4KB
                    return 'text',f"二进制文件内容 (前4KB): {content.hex()[:500]}..."
            except Exception as e:
                print(f"无法读取文件 {file_path}: {e}")
                return None, None
        except Exception as e:
            print(f"无法读取文件 {file_path}: {e}")
            return None, None
                    
    def handle_file(self, file_path,mode='r',data=None):
        """处理文件"""
        if not os.path.isfile(file_path):
            print(f"文件不存在: {file_path}")
            return None, None

        file_type,handled_result = None, None
        for h in self.register_handlers:
            if h["handler"].can_handle(file_path):
               file_type, handled_result = h["handler"].handle_file(file_path,mode,data)
               if handled_result:
                   break
        else:    
            if mode == 'r':
                log_print(f"使用默认文件处理器读取文件内容: {file_path}")
                file_type, handled_result =self.default_file_handler(file_path)
            else:
                log_print(f"未找到模式为'{mode}'的处理器: {file_path}")
        return file_type, handled_result

gRWReghandlers=RWRegHandlers()

def get_RWRegHandlers():
    """获取已注册的文件处理器"""
    return gRWReghandlers