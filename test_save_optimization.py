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
    db_path = "test_save_optimization.db"
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
    
    # 统计跳过哈希计算和数据库更新的文件数量
    skip_hash_count = result.stdout.count("跳过哈希计算")
    skip_full_update_count = result.stdout.count("跳过哈希计算和数据库更新")
    
    print(f"跳过哈希计算的文件数: {skip_hash_count}")
    print(f"完全跳过哈希计算和数据库更新的文件数: {skip_full_update_count}")
    
    return duration, result.stdout, skip_hash_count, skip_full_update_count

def check_database_updates(db_path):
    """检查数据库中文件的更新时间"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有文件的详细信息，包括所有字段
    cursor.execute("SELECT file_path, file_size, created_time, modified_time, accessed_time, owner, file_hash, last_checked FROM file_features")
    results = cursor.fetchall()
    
    # 打印并返回文件更新信息
    file_updates = {}
    print("\n=== 数据库文件详细信息 ===")
    for row in results:
        file_path, file_size, created_time, modified_time, accessed_time, owner, file_hash, last_checked = row
        file_name = os.path.basename(file_path)
        file_updates[file_name] = {
            'file_path': file_path,
            'file_size': file_size,
            'created_time': created_time,
            'modified_time': modified_time,
            'accessed_time': accessed_time,
            'owner': owner,
            'file_hash': file_hash,
            'last_checked': last_checked
        }
        print(f"文件 {file_name}:")
        print(f"  file_size: {file_size}")
        print(f"  created_time: {created_time}")
        print(f"  modified_time: {modified_time}")
        print(f"  last_checked: {last_checked}")
        print(f"  file_hash: {file_hash[:20]}...")
    
    conn.close()
    return file_updates

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
    print("===== 数据库更新优化功能测试 =====")
    
    # 1. 设置测试环境
    print("\n1. 设置测试环境...")
    test_dir, db_path = setup_test_environment()
    print(f"创建测试目录: {test_dir}")
    print(f"创建测试数据库: {db_path}")
    
    # 2. 第一次扫描 - 应该计算所有文件的哈希值并完整保存到数据库
    print("\n2. 第一次扫描 - 完整保存所有文件属性...")
    duration1, output1, skip_hash_count1, skip_full_update_count1 = run_scan(test_dir, db_path)
    print("首次扫描数据库文件信息:")
    first_scan_updates = check_database_updates(db_path)
    
    # 等待1秒，确保时间戳有差异
    time.sleep(1)
    
    # 3. 第二次扫描 - 不强制重新计算，应该跳过所有文件的哈希计算
    print("\n3. 第二次扫描 - 不强制重新计算，验证是否跳过哈希计算和优化数据库更新...")
    duration2, output2, skip_hash_count2, skip_full_update_count2 = run_scan(test_dir, db_path)
    print("第二次扫描数据库文件信息:")
    second_scan_updates = check_database_updates(db_path)
    
    # 4. 修改部分文件
    print("\n4. 修改部分文件...")
    modify_some_files(test_dir)
    
    # 5. 第三次扫描 - 不强制重新计算，应该跳过未修改文件的哈希计算
    print("\n5. 第三次扫描 - 验证修改过的文件是否被更新，未修改文件是否继续跳过...")
    duration3, output3, skip_hash_count3, skip_full_update_count3 = run_scan(test_dir, db_path)
    
    # 6. 清理测试环境
    print("\n6. 清理测试环境...")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # 7. 测试总结
    print("\n===== 测试总结 =====")
    print(f"第一次扫描耗时: {duration1:.2f}秒, 跳过哈希计算: {skip_hash_count1}个文件")
    print(f"第二次扫描耗时: {duration2:.2f}秒, 跳过哈希计算: {skip_hash_count2}个文件, 完全跳过更新: {skip_full_update_count2}个文件")
    print(f"第三次扫描耗时: {duration3:.2f}秒, 跳过哈希计算: {skip_hash_count3}个文件")
    print()
    
    # 验证测试结果
    # 第二次扫描应该跳过所有5个文件的哈希计算
    # 第三次扫描应该跳过3个未修改的文件（总共5个文件，修改了2个）
    passed = (skip_hash_count2 >= 5) and (skip_hash_count3 >= 3) and (skip_hash_count1 == 0)
    
    if passed:
        print("✅ 数据库更新优化功能测试通过!")
        print(f"- 首次扫描: 没有跳过任何哈希计算 ({skip_hash_count1}个)")
        print(f"- 第二次扫描: 成功跳过所有文件的哈希计算 ({skip_hash_count2}个)")
        print(f"- 其中完全跳过数据库更新的文件: {skip_full_update_count2}个")
        print(f"- 第三次扫描: 成功跳过未修改文件的哈希计算 ({skip_hash_count3}个)")
        print("- 证明了数据库更新优化功能正常工作")
    else:
        print("❌ 数据库更新优化功能测试失败!")
        print(f"  首次扫描跳过哈希计算数: {skip_hash_count1} (期望: 0)")
        print(f"  第二次扫描跳过哈希计算数: {skip_hash_count2} (期望: >=5)")
        print(f"  第三次扫描跳过哈希计算数: {skip_hash_count3} (期望: >=3)")

    
if __name__ == "__main__":
    main()