import os
import shutil
import time
import subprocess
import sqlite3
from datetime import datetime

def setup_test_environment():
    """设置测试环境"""
    # 创建测试目录
    test_dir = os.path.join(os.getcwd(), "test_dir")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    # 创建几个测试文件
    for i in range(5):
        file_path = os.path.join(test_dir, f"test_file_{i}.txt")
        with open(file_path, "w") as f:
            f.write(f"This is test content {i} for file {i}")
    
    # 创建测试数据库
    db_path = "test_db.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    return test_dir, db_path

def run_scan(directory, db_path, force_recalculate=False):
    """运行文件扫描"""
    cmd = ["python", "file_duplicate_finder.py", directory, "--db", db_path]
    if force_recalculate:
        cmd.append("--force-recalculate")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"扫描完成，耗时: {duration:.2f}秒")
    print(f"标准输出: {result.stdout}")
    print(f"标准错误: {result.stderr}")
    
    return duration, result.stdout

def check_database(db_path):
    """检查数据库中的文件记录"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM file_features")
    count = cursor.fetchone()[0]
    
    print(f"数据库中文件记录数量: {count}")
    
    conn.close()
    return count

def modify_some_files(directory):
    """修改部分文件以测试增量更新"""
    # 只修改奇数编号的文件
    for i in range(5):
        if i % 2 == 1:
            file_path = os.path.join(directory, f"test_file_{i}.txt")
            with open(file_path, "a") as f:
                f.write(f"\nModified at {datetime.now().isoformat()}")
    
    print(f"已修改文件: test_file_1.txt, test_file_3.txt")

def main():
    print("===== 哈希计算优化功能测试 =====")
    
    # 1. 设置测试环境
    print("\n1. 设置测试环境...")
    test_dir, db_path = setup_test_environment()
    print(f"创建测试目录: {test_dir}")
    print(f"创建测试数据库: {db_path}")
    
    # 2. 第一次扫描 - 应该计算所有文件的哈希值
    print("\n2. 第一次扫描 - 计算所有文件的哈希值...")
    duration1, output1 = run_scan(test_dir, db_path)
    check_database(db_path)
    
    # 3. 第二次扫描 - 不强制重新计算，应该跳过所有文件的哈希计算
    print("\n3. 第二次扫描 - 不强制重新计算哈希值...")
    duration2, output2 = run_scan(test_dir, db_path)
    
    # 检查是否有"跳过哈希计算"的日志
    skipped_count = output2.count("跳过哈希计算")
    print(f"跳过哈希计算的文件数量: {skipped_count}")
    
    # 4. 修改部分文件
    print("\n4. 修改部分文件...")
    modify_some_files(test_dir)
    
    # 5. 第三次扫描 - 不强制重新计算，应该只重新计算修改过的文件
    print("\n5. 第三次扫描 - 不强制重新计算哈希值(部分文件已修改)...")
    duration3, output3 = run_scan(test_dir, db_path)
    
    # 检查是否有"跳过哈希计算"的日志
    skipped_count_after_modify = output3.count("跳过哈希计算")
    recalculated_count_after_modify = 5 - skipped_count_after_modify
    print(f"跳过哈希计算的文件数量: {skipped_count_after_modify}")
    print(f"重新计算哈希的文件数量: {recalculated_count_after_modify}")
    
    # 6. 第四次扫描 - 强制重新计算所有文件的哈希值
    print("\n6. 第四次扫描 - 强制重新计算所有文件的哈希值...")
    duration4, output4 = run_scan(test_dir, db_path, force_recalculate=True)
    
    # 检查是否有"跳过哈希计算"的日志
    skipped_count_force = output4.count("跳过哈希计算")
    print(f"跳过哈希计算的文件数量: {skipped_count_force}")
    
    # 7. 清理测试环境
    print("\n7. 清理测试环境...")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 8. 测试总结
    print("\n===== 测试总结 =====")
    print(f"第一次扫描耗时: {duration1:.2f}秒")
    print(f"第二次扫描耗时: {duration2:.2f}秒")
    print(f"第三次扫描耗时: {duration3:.2f}秒")
    print(f"第四次扫描耗时: {duration4:.2f}秒")
    print()
    
    # 验证测试结果
    if skipped_count >= 5 and skipped_count_force == 0 and recalculated_count_after_modify == 2:
        print("✅ 哈希计算优化功能测试通过!")
    else:
        print("❌ 哈希计算优化功能测试失败!")
    
if __name__ == "__main__":
    main()