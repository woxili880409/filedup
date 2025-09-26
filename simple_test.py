import os
import sys

"""简单的测试脚本，用于验证文件重复查找器是否能正常运行"""

def main():
    # 创建一个简单的测试文件
    test_file_path = "test_data.txt"
    with open(test_file_path, "w") as f:
        f.write("这是一个测试文件\n用于验证文件重复查找器是否能正常工作\n")
    
    print(f"已创建测试文件: {test_file_path}")
    print("\n现在测试文件重复查找器是否能正常运行...\n")
    
    # 测试命令：扫描当前目录
    print("="*60)
    print("测试1: 扫描当前目录")
    print("="*60)
    os.system(f"{sys.executable} file_duplicate_finder.py .")
    
    # 清理测试文件
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
        print(f"\n已删除测试文件: {test_file_path}")
    
    print("\n测试完成！")
    print("如果程序正常运行，您应该可以看到扫描结果。")
    print("检查是否生成了file_features.db文件。")


if __name__ == "__main__":
    main()