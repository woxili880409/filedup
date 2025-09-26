import os
import hashlib
import shutil

"""
测试哈希算法功能的脚本
该脚本创建测试文件并验证不同哈希算法的计算结果
"""

# 创建临时测试目录
test_dir = "test_hash_dir"
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

try:
    # 创建测试文件1: 小文本文件
    test_file1 = os.path.join(test_dir, "small_test.txt")
    with open(test_file1, "w", encoding="utf-8") as f:
        f.write("这是一个用于测试哈希算法的小文件内容。\n")
        f.write("包含多行文本数据。\n")
    
    # 创建测试文件2: 稍微大一点的文件（约1MB）
    test_file2 = os.path.join(test_dir, "medium_test.dat")
    with open(test_file2, "wb") as f:
        # 写入约1MB的数据
        for i in range(1024 * 128):  # 128KB
            f.write(bytes(f"这是测试数据块 #{i} " * 4, "utf-8"))
    
    print("已创建测试文件。")
    print(f"测试文件1: {test_file1} ({os.path.getsize(test_file1)} 字节)")
    print(f"测试文件2: {test_file2} ({os.path.getsize(test_file2)} 字节)")
    
    # 测试使用不同算法计算哈希值
    print("\n测试不同哈希算法计算结果：")
    
    # 测试我们的file_duplicate_finder.py中的calculate_file_hash方法
    print("\n测试file_duplicate_finder.py中的哈希计算:")
    
    # 导入FileDuplicateFinder类
    import importlib.util
    spec = importlib.util.spec_from_file_location("file_duplicate_finder", "file_duplicate_finder.py")
    file_duplicate_finder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(file_duplicate_finder)
    
    # 创建一个临时的FileDuplicateFinder实例
    finder = file_duplicate_finder.FileDuplicateFinder(db_path=":memory:")
    
    # 测试不同算法
    for algorithm in ['md5', 'sha1', 'sha256']:
        print(f"\n使用{algorithm}算法:")
        
        # 计算文件哈希
        hash1 = finder.calculate_file_hash(test_file1, hash_algorithm=algorithm)
        hash2 = finder.calculate_file_hash(test_file2, hash_algorithm=algorithm)
        
        print(f"文件1的哈希值: {hash1}")
        print(f"文件2的哈希值: {hash2}")
        
        # 验证使用标准库直接计算的结果是否一致
        def verify_hash(file_path, algo):
            hasher = hashlib.new(algo)
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while buf:
                    hasher.update(buf)
                    buf = f.read(65536)
            return f"{algo}:{hasher.hexdigest()}"
        
        verify_hash1 = verify_hash(test_file1, algorithm)
        verify_hash2 = verify_hash(test_file2, algorithm)
        
        # 验证结果
        assert hash1 == verify_hash1, f"{algorithm}算法计算的文件1哈希值不一致！"
        assert hash2 == verify_hash2, f"{algorithm}算法计算的文件2哈希值不一致！"
        print(f"✓ {algorithm}算法计算结果正确。")
    
    print("\n所有哈希算法测试通过！")
    
finally:
    # 清理测试文件和目录
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print("\n已清理测试文件和目录。")