import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

"""测试文件重复查找器的脚本"""

def create_test_directory(base_path):
    """创建测试目录结构和文件"""
    # 删除旧的测试目录
    if os.path.exists(base_path):
        shutil.rmtree(base_path)
        time.sleep(1)  # 给系统一些时间来删除目录
    
    # 创建测试目录结构
    os.makedirs(base_path, exist_ok=True)
    
    # 创建一些测试文件
    # 1. 创建原始文件
    with open(os.path.join(base_path, "original.txt"), "w") as f:
        f.write("这是一个测试文件\n用于测试文件重复查找器\n")
        
    with open(os.path.join(base_path, "document.pdf"), "w") as f:
        f.write("这是一个模拟的PDF文件内容")
        
    with open(os.path.join(base_path, "image.jpg"), "w") as f:
        f.write("这是一个模拟的图像文件内容")
        
    shutil.copy2(os.path.join(os.path.dirname(__file__) , "./word_test.docx"), os.path.join(base_path, "document.docx") )
    
    # 2. 创建子目录和重复文件
    subdir1 = os.path.join(base_path, "subdir1")
    os.makedirs(subdir1, exist_ok=True)
    
    # 复制文件以创建重复项
    shutil.copy2(os.path.join(base_path, "original.txt"), os.path.join(subdir1, "duplicate1.txt"))
    shutil.copy2(os.path.join(base_path, "document.pdf"), os.path.join(subdir1, "doc_copy.pdf"))
    
    # 创建另一个子目录
    subdir2 = os.path.join(base_path, "subdir2")
    os.makedirs(subdir2, exist_ok=True)
    
    # 创建更多重复文件
    shutil.copy2(os.path.join(base_path, "original.txt"), os.path.join(subdir2, "duplicate2.txt"))
    shutil.copy2(os.path.join(base_path, "image.jpg"), os.path.join(subdir2, "img_copy.jpg"))
    
    # 创建一个唯一的新文件
    with open(os.path.join(subdir2, "unique.txt"), "w") as f:
        f.write("这是一个唯一的文件，没有重复项")
    
    print(f"测试目录已创建: {base_path}")
    print("目录结构:")
    for root, dirs, files in os.walk(base_path):
        level = root.replace(base_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        for file in files:
            print(f"{indent}    {file}")
    
    return base_path

def run_command(command):
    """运行命令并返回输出"""
    print(f"\n运行命令: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            encoding="utf-8"
        )
        if result.stdout:
            print("输出:")
            print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)
        return result.returncode
    except Exception as e:
        print(f"命令执行失败: {e}")
        return -1

def main():
    # 测试目录路径
    test_dir = os.path.join(os.getcwd(), "test_files")
    db_file = "test_db.db"
    
    # 确保测试数据文件不存在
    if os.path.exists(db_file):
        os.remove(db_file)
    
    # 步骤1: 创建测试目录和文件
    print("="*60)
    print("步骤1: 创建测试目录和文件")
    print("="*60)
    create_test_directory(test_dir)
    
    # 步骤2: 扫描目录并创建数据文件
    print("\n" + "="*60)
    print("步骤2: 扫描目录并创建数据文件")
    print("="*60)
    # 使用输入流模拟用户选择
    # 我们将创建一个临时Python脚本来自动化交互
    auto_script = """# -*- coding: utf-8 -*-
import sys
import subprocess

# 运行扫描命令，并自动回答"n"不查找重复文件
proc = subprocess.Popen(
    [sys.executable, 'file_duplicate_finder.py', r'%s', '--db', r'%s'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding="utf-8",
    text=True
)

# 等待程序提示，然后发送'n'
output, error = proc.communicate(input='n\\n')
print(output)
if error:
    print(error)
""" % (test_dir, db_file)
    
    with open("auto_scan.py", "w") as f:
        f.write(auto_script)
    
    # 运行自动扫描脚本
    run_command([sys.executable, "auto_scan.py"])
    os.remove("auto_scan.py")  # 清理临时脚本
    
    # 步骤3: 查找重复文件
    print("\n" + "="*60)
    print("步骤3: 查找重复文件")
    print("="*60)
    run_command([sys.executable, "file_duplicate_finder.py", test_dir, "--find-duplicates", "--db", db_file])
    
    # 步骤4: 修改目录（添加、删除、更新文件）
    print("\n" + "="*60)
    print("步骤4: 修改目录结构")
    print("="*60)
    
    # 删除一个文件
    file_to_delete = os.path.join(test_dir, "document.pdf")
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)
        print(f"已删除文件: {file_to_delete}")
    
    # 更新一个文件
    file_to_update = os.path.join(test_dir, "original.txt")
    with open(file_to_update, "a") as f:
        f.write("这是更新的内容\n")
    print(f"已更新文件: {file_to_update}")
    
    # 添加一个新文件
    new_file = os.path.join(test_dir, "new_file.txt")
    with open(new_file, "w") as f:
        f.write("这是一个新添加的文件\n")
    print(f"已添加新文件: {new_file}")
    
    # 步骤5: 比较目录变更
    print("\n" + "="*60)
    print("步骤5: 比较目录变更")
    print("="*60)
    # 创建自动比较脚本
    auto_compare_script = """# -*- coding: utf-8 -*-
import sys
import subprocess

# 运行比较命令，并自动回答"n"不更新数据
proc = subprocess.Popen(
    [sys.executable, 'file_duplicate_finder.py', r'%s', '--compare', '--db', r'%s'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding="utf-8",
    text=True
)

# 等待程序提示，然后发送'n'
output, error = proc.communicate(input='n\\n')
print(output)
if error:
    print(error)
""" % (test_dir, db_file)
    
    with open("auto_compare.py", "w", encoding="utf-8") as f:
        f.write(auto_compare_script)
    
    # 运行自动比较脚本
    run_command([sys.executable, "auto_compare.py"])
    os.remove("auto_compare.py")  # 清理临时脚本
    
    # 步骤6: 读取文件内容
    print("\n" + "="*60)
    print("步骤6: 读取文件内容")
    print("="*60)
    file_to_read = os.path.join(test_dir, "document.docx")
    run_command([sys.executable, "file_duplicate_finder.py", test_dir, "--read-file", file_to_read, "--db", db_file])
    
    # 步骤7: 清理（可选）
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print("您可以手动清理测试目录和数据文件：")
    print(f"- 测试目录: {test_dir}")
    print(f"- 数据文件: {db_file}")


if __name__ == "__main__":
    main()