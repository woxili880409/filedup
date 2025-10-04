import sys
import os

"""
查找Python安装目录和dlls文件夹的脚本
用于解决SQLite3导入错误：ImportError: DLL load failed while importing _sqlite3
"""

def find_python_dlls_directory():
    """查找Python的dlls目录位置"""
    # 获取Python解释器的安装路径
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    
    # 查找标准的dlls目录
    dlls_dir = os.path.join(python_dir, 'DLLs')
    
    # 检查dlls目录是否存在
    dlls_exists = os.path.isdir(dlls_dir)
    
    # 显示相关信息
    print(f"Python解释器路径: {python_exe}")
    print(f"Python安装目录: {python_dir}")
    print(f"DLLs目录路径: {dlls_dir}")
    print(f"DLLs目录是否存在: {'是' if dlls_exists else '否'}")
    
    # 检查_sqlite3.pyd文件是否存在
    sqlite3_pyd = os.path.join(dlls_dir, '_sqlite3.pyd')
    if os.path.exists(sqlite3_pyd):
        print(f"_sqlite3.pyd文件存在: {sqlite3_pyd}")
    else:
        print(f"警告: 未找到_sqlite3.pyd文件")
    
    # 提供解决方案建议
    print("\n" + "="*60)
    print("解决方案建议")
    print("="*60)
    print("1. 下载SQLite3的DLL文件:")
    print("   访问 https://www.sqlite.org/download.html")
    print("   对于Windows 64位系统，下载 'sqlite-dll-win64-x64-*.zip'")
    print("   对于Windows 32位系统，下载 'sqlite-dll-win32-x86-*.zip'")
    print()
    print("2. 解压下载的文件，得到 sqlite3.dll 文件")
    print()
    print(f"3. 将 sqlite3.dll 复制到以下目录:")
    print(f"   {dlls_dir}")
    print()
    print("4. 如果问题仍然存在，尝试重新安装Python并确保勾选SQLite3选项")
    print()
    print("5. 确保已安装Visual C++ Redistributable，这可能是许多DLL加载问题的原因")

if __name__ == "__main__":
    print("正在查找Python DLLs目录...\n")
    find_python_dlls_directory()