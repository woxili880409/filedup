import os
import sys
import hashlib
import sqlite3
import datetime
import json
import argparse
import getpass
import os
import threading
import queue
from pathlib import Path
import json
from tkinter import NO
from filedup.prograss import ProgressBar
# from itertools import batched
# 注册的处理器文件名
from filedup.global_vars import FILE_FEATURES_DB_FILENAME, FILE_DUMP_FILENAME, log_print
from filedup.rw_reg_handlers import RWRegHandlers, get_RWRegHandlers

class FileDuplicateFinder:
    def __init__(self, db_path=FILE_FEATURES_DB_FILENAME, max_threads=4, hash_algorithm='md5', force_recalculate=False):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.max_threads = max_threads
        self.hash_algorithm = hash_algorithm
        self.force_recalculate = force_recalculate
        # self.register_handlers=[] #[{"ext":None,"handler":rw_interface.RWInterface}]
        self.progress_bar=None
        self.rw_reg_handlers:RWRegHandlers = get_RWRegHandlers() # 注册文件处理器
        self.initialize_database()
        
        
    def get_existing_file_info(self):
        """获取数据库中所有文件的信息，用于在多线程扫描前判断是否需要重新计算哈希值和保存文件属性"""
        file_info = {}
        try:
            self.cursor.execute("SELECT file_path, file_size, modified_time, file_hash, created_time, accessed_time, owner FROM file_features")
            for row in self.cursor.fetchall():
                file_path, file_size, modified_time, file_hash, created_time, accessed_time, owner = row
                file_info[file_path] = {
                    'size': file_size,
                    'modified_time': modified_time,
                    'hash': file_hash,
                    'created_time': created_time,
                    'accessed_time': accessed_time,
                    'owner': owner
                }
        except sqlite3.Error as e:
            print(f"获取已有文件信息时出错: {e}")
        return file_info
        
    def initialize_database(self):
        """初始化SQLite数据库，创建文件特征表"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # 启用WAL模式，提高并发性能
            self.conn.execute('PRAGMA journal_mode = WAL')
            # 增加缓存大小到约64MB（负值表示KB）
            self.conn.execute('PRAGMA cache_size = -65536')
            # 设置同步模式为NORMAL，平衡性能和安全性
            self.conn.execute('PRAGMA synchronous = NORMAL')
            
            self.cursor = self.conn.cursor()
            # 创建文件特征表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    created_time TEXT,
                    modified_time TEXT,
                    accessed_time TEXT,
                    owner TEXT,
                    file_hash TEXT,
                    last_checked TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"数据库初始化错误: {e}")
    
    def calculate_file_hash(self, file_path, block_size=1048576, hash_algorithm='md5'):
        """计算文件的哈希值
        
        Args:
            file_path: 文件路径
            block_size: 读取块大小，默认1048576字节
            hash_algorithm: 哈希算法，可选'md5'、'sha1'、'sha256'，默认'md5'
            
        Returns:
            哈希值字符串，如果出错则返回None
        """
        # 验证哈希算法
        if hash_algorithm not in hashlib.algorithms_available:
            print(f"不支持的哈希算法: {hash_algorithm}，使用md5")
            hash_algorithm = 'md5'
        
        try:
            # 创建哈希对象
            hasher = hashlib.new(hash_algorithm)
            
            # 获取文件大小用于进度显示
            file_size = os.path.getsize(file_path)
            processed_size = 0
            
            # 读取整个文件计算哈希值
            with open(file_path, 'rb') as file:
                buf = file.read(block_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    processed_size += len(buf)
                    buf = file.read(block_size)
                    
                    # 对于大文件显示进度
                    if file_size > 100 * 1024 * 1024:  # 大于100MB的文件
                        progress = (processed_size / file_size) * 100
                        # 每10%进度显示一次
                        if int(progress) % 10 == 0 and int((processed_size - len(buf)) / file_size * 100) % 10 != 0:
                            print(f"计算文件哈希 {os.path.basename(file_path)}: {progress:.1f}%")
            
            # 返回带算法前缀的哈希值，便于区分
            return f"{hash_algorithm}:{hasher.hexdigest()}"
            
        except (PermissionError, FileNotFoundError) as e:
            print(f"无法计算文件哈希 {file_path}: {e}")
            return None
        except Exception as e:
            print(f"计算哈希时发生未知错误 {file_path}: {e}")
            return None
            
    def _worker_thread(self, file_queue, result_queue, existing_file_info):
        """工作线程函数，从队列获取文件并计算哈希值（支持选择性哈希计算和属性保存）"""
        while True:
            try:
                file_path = file_queue.get(block=False)
                if self.progress_bar:
                    self.progress_bar.update()
                try:
                    # 获取文件属性
                    file_stats = os.stat(file_path)
                    created_time = datetime.datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                    modified_time = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    accessed_time = datetime.datetime.fromtimestamp(file_stats.st_atime).isoformat()
                    file_size = file_stats.st_size
                    file_owner = self.get_file_owner(file_path)
                    current_time = datetime.datetime.now().isoformat()
                    
                    # 决定是否需要重新计算哈希值
                    need_recalculate = self.force_recalculate
                    file_hash = None
                    needs_update = self.force_recalculate  # 默认需要更新
                    
                    if not self.force_recalculate and file_path in existing_file_info:
                        # 检查文件大小和修改时间是否变化
                        existing_info = existing_file_info[file_path]
                        
                        # 检查是否所有属性都相同
                        if (existing_info['size'] == file_size and 
                            existing_info['modified_time'] == modified_time and
                            existing_info['created_time'] == created_time and
                             existing_info['owner'] == file_owner):
                            # existing_info['accessed_time'] == accessed_time and
                           
                            # 所有属性都未变更，使用数据库中的哈希值
                            file_hash = existing_info['hash']
                            log_print(f"跳过哈希计算和数据库更新 {file_path} (所有属性未变更)")
                            need_recalculate = False
                            needs_update = False  # 不需要更新数据库
                        else:
                            # 属性有变更，但大小或修改时间未变，可能只需要更新其他属性
                            if existing_info['size'] == file_size and existing_info['modified_time'] == modified_time:
                                file_hash = existing_info['hash']
                                log_print(f"跳过哈希计算 {file_path} (大小和修改时间未变更)")
                                need_recalculate = False
                            else:
                                need_recalculate = True
                    else:
                        need_recalculate = True
                    
                    if need_recalculate or not file_hash:
                        # 需要重新计算哈希值
                        file_hash = self.calculate_file_hash(file_path, hash_algorithm=self.hash_algorithm)
                        needs_update = True  # 哈希值变化，需要更新数据库
                    
                    if file_hash:
                        # 只有在需要更新或文件是新的时才放入结果队列
                        if needs_update or file_path not in existing_file_info:
                            attributes = {
                                'file_path': file_path,
                                'file_size': file_size,
                                'created_time': created_time,
                                'modified_time': modified_time,
                                'accessed_time': accessed_time,
                                'owner': file_owner,
                                'file_hash': file_hash,
                                'last_checked': current_time,
                                'needs_update': needs_update
                            }
                            result_queue.put(attributes)
                        else:
                            # 更新last_checked时间，但不做其他更改
                            attributes = {
                                'file_path': file_path,
                                'file_size': file_size,
                                'created_time': created_time,
                                'modified_time': modified_time,
                                'accessed_time': accessed_time,
                                'owner': file_owner,
                                'file_hash': file_hash,
                                'last_checked': current_time,
                                'needs_update': False
                            }
                            result_queue.put(attributes)
                except Exception as e:
                    print(f"处理文件时出错 {file_path}: {e}")
                finally:
                    file_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                print(f"工作线程错误: {e}")
                break
    
    def get_file_owner(self, file_path):
        """获取文件所有者信息"""
        try:
            # 在Windows上使用getpass获取当前用户
            if os.name == 'nt':
                return getpass.getuser()
            else:
                # 在Unix/Linux系统上使用os.stat获取所有者
                import pwd
                stat_info = os.stat(file_path)
                return pwd.getpwuid(stat_info.st_uid).pw_name
        except Exception as e:
            print(f"无法获取文件所有者 {file_path}: {e}")
            return "unknown"
    
    def get_file_attributes(self, file_path,recalculate_hash=True):
        """获取文件的属性信息"""
        try:
            file_stats = os.stat(file_path)
            # 转换时间戳为可读格式
            created_time = datetime.datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            modified_time = datetime.datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            accessed_time = datetime.datetime.fromtimestamp(file_stats.st_atime).isoformat()
            
            file_size = file_stats.st_size
            file_owner = self.get_file_owner(file_path)
            # 计算哈希值
            if recalculate_hash:
                file_hash = self.calculate_file_hash(file_path)
            else:
                file_hash = None
            current_time = datetime.datetime.now().isoformat()
            
            return {
                'file_path': file_path,
                'file_size': file_size,
                'created_time': created_time,
                'modified_time': modified_time,
                'accessed_time': accessed_time,
                'owner': file_owner,
                'file_hash': file_hash,
                'last_checked': current_time
            }
        except Exception as e:
            print(f"无法获取文件属性 {file_path}: {e}")
            return None
    
    def save_file_attributes(self, attributes):
        """保存文件属性到数据库，支持选择性更新（单文件版本）"""
        if not attributes or 'file_hash' not in attributes or attributes['file_hash'] is None:
            return False
            
        try:
            # 规范化文件路径，确保在数据库中存储一致的格式
            normalized_path = os.path.normpath(attributes['file_path'])
            
            # 检查文件是否已存在于数据库中（使用规范化后的路径）
            self.cursor.execute("SELECT id FROM file_features WHERE file_path = ?", (normalized_path,))
            existing_file = self.cursor.fetchone()
            
            if existing_file:
                # 检查是否需要全面更新
                if 'needs_update' in attributes and not attributes['needs_update']:
                    # 只更新last_checked时间
                    self.cursor.execute(
                        "UPDATE file_features SET last_checked = ? WHERE file_path = ?",
                        (attributes['last_checked'], normalized_path)
                    )
                    return True
                    
                # 更新现有文件的所有属性
                self.cursor.execute('''
                    UPDATE file_features
                    SET file_size = ?, created_time = ?, modified_time = ?, accessed_time = ?,
                        owner = ?, file_hash = ?, last_checked = ?
                    WHERE file_path = ?
                ''', (
                    attributes['file_size'], attributes['created_time'], attributes['modified_time'],
                    attributes['accessed_time'], attributes['owner'], attributes['file_hash'],
                    attributes['last_checked'], normalized_path
                ))
            else:
                # 插入新文件（使用规范化后的路径）
                self.cursor.execute('''
                    INSERT INTO file_features (
                        file_path, file_size, created_time, modified_time, accessed_time,
                        owner, file_hash, last_checked
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    normalized_path, attributes['file_size'], attributes['created_time'],
                    attributes['modified_time'], attributes['accessed_time'], attributes['owner'],
                    attributes['file_hash'], attributes['last_checked']
                ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存文件属性错误: {e}")
            self.conn.rollback()
            return False
            
    def batch_save_file_attributes(self, attributes_list,show_ditail=False):
        """批量保存文件属性到数据库，使用事务提高性能"""
        if not attributes_list:
            return False
            
        try:
            # 开始事务
            self.cursor.execute('BEGIN TRANSACTION')
            
            for attributes in attributes_list:
                if show_ditail:
                    print(f"处理文件: {attributes['file_path']}")
                if not attributes or 'file_hash' not in attributes or attributes['file_hash'] is None:
                    continue
                     
                # 规范化文件路径，确保在数据库中存储一致的格式
                normalized_path = os.path.normpath(attributes['file_path'])
                
                # 检查文件是否已存在于数据库中（使用规范化后的路径）
                self.cursor.execute("SELECT id FROM file_features WHERE file_path = ?", (normalized_path,))
                existing_file = self.cursor.fetchone()
                
                if existing_file:
                    # 检查是否需要全面更新
                    if 'needs_update' in attributes and not attributes['needs_update']:
                        # 只更新last_checked时间
                        self.cursor.execute(
                            "UPDATE file_features SET last_checked = ? WHERE file_path = ?",
                            (attributes['last_checked'], normalized_path)
                        )
                        continue
                     
                    # 更新现有文件的所有属性
                    self.cursor.execute('''
                        UPDATE file_features
                        SET file_size = ?, created_time = ?, modified_time = ?, accessed_time = ?,
                            owner = ?, file_hash = ?, last_checked = ?
                        WHERE file_path = ?
                    ''', (
                        attributes['file_size'], attributes['created_time'], attributes['modified_time'],
                        attributes['accessed_time'], attributes['owner'], attributes['file_hash'],
                        attributes['last_checked'], normalized_path
                    ))
                else:
                    # 插入新文件（使用规范化后的路径）
                    self.cursor.execute('''
                        INSERT INTO file_features (
                            file_path, file_size, created_time, modified_time, accessed_time,
                            owner, file_hash, last_checked
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        normalized_path, attributes['file_size'], attributes['created_time'],
                        attributes['modified_time'], attributes['accessed_time'], attributes['owner'],
                        attributes['file_hash'], attributes['last_checked']
                    ))
            
            # 一次性提交所有更改
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"批量保存文件属性错误: {e}")
            self.conn.rollback()
            return False
    
    def scan_directory(self, directory_path):
        """扫描目录及其子目录中的所有文件（多线程版本，支持批量处理）"""
        if not os.path.isdir(directory_path):
            print(f"目录不存在: {directory_path}")
            return 0
            
        # 收集所有文件路径
        all_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and not os.path.islink(file_path):
                    if os.name == 'nt':
                        file_path = os.path.realpath(file_path)  # 确保路径是真实路径名称
                    all_files.append(file_path)
        
        total_files = len(all_files)
        if total_files == 0:
            print("未找到任何文件。")
            return 0
            
        # 在主线程中获取现有文件信息，避免在工作线程中访问数据库
        existing_file_info = {} if self.force_recalculate else self.get_existing_file_info()
        
        print(f"找到 {total_files} 个文件，开始使用 {self.max_threads} 个线程并行处理...")
        
        # 创建队列
        file_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # 填充文件队列
        for file_path in all_files:
            file_queue.put(file_path)
        
        self.progress_bar = ProgressBar(total_files)
               
        # 创建并启动工作线程
        threads = []
        for _ in range(min(self.max_threads, total_files)):
            # 将现有文件信息传递给工作线程，避免工作线程直接访问数据库
            thread = threading.Thread(target=self._worker_thread, args=(file_queue, result_queue, existing_file_info))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有工作线程完成
        for thread in threads:
            thread.join()
        
        # 关闭进度条
        if self.progress_bar:
            self.progress_bar.finish()

        # 批量处理结果
        batch_size = 1000  # 每批处理的文件数
        attributes_batch = []
        processed_count = 0
        
        print("开始批量保存文件属性...")
        while not result_queue.empty():
            attributes = result_queue.get()
            if attributes:
                attributes_batch.append(attributes)
                processed_count += 1
                
                # 当达到批处理大小时，批量保存
                if len(attributes_batch) >= batch_size:
                    self.batch_save_file_attributes(attributes_batch)
                    attributes_batch = []
                    # 显示进度
                    print(f"已保存 {processed_count}/{total_files} 个文件的属性")
        
        # 保存剩余的文件属性
        if attributes_batch:
            self.batch_save_file_attributes(attributes_batch)
            print(f"已保存 {processed_count}/{total_files} 个文件的属性")
        
        print(f"处理完成，共保存 {processed_count} 个文件的属性。")
        return processed_count
    
    def find_duplicate_files(self):
        """查找数据库中的重复文件"""
        try:
            # 查找具有相同哈希值的文件组
            self.cursor.execute('''
                SELECT file_hash, GROUP_CONCAT(file_path, '|') as file_paths
                FROM file_features
                GROUP BY file_hash
                HAVING COUNT(*) > 1
            ''')
            duplicates = self.cursor.fetchall()
            
            result = []
            for file_hash, file_paths_str in duplicates:
                file_paths = file_paths_str.split('|')
                # 获取每个文件的详细信息
                files_info = []
                for file_path in file_paths:
                    self.cursor.execute(
                        "SELECT file_size, created_time, modified_time, owner FROM file_features WHERE file_path = ?",
                        (file_path,)
                    )
                    file_info = self.cursor.fetchone()
                    if file_info:
                        files_info.append({
                            'path': file_path,
                            'size': file_info[0],
                            'created': file_info[1],
                            'modified': file_info[2],
                            'owner': file_info[3]
                        })
                result.append({
                    'hash': file_hash,
                    'files': files_info
                })
            
            return result
        except sqlite3.Error as e:
            print(f"查找重复文件错误: {e}")
            return []
    
    def compare_with_database(self, directory_path, recalculate_hash=True):
        """比较目录中的文件与数据库中的记录"""
        if not os.path.isdir(directory_path):
            print(f"目录不存在: {directory_path}")
            return {}
            
        # 获取数据库中所有文件路径
        self.cursor.execute("SELECT file_path FROM file_features")
        db_files = {row[0] for row in self.cursor.fetchall()}
        
        # 扫描目录中的文件
        current_files = set()
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and not os.path.islink(file_path):
                    current_files.add(file_path)
        
        # 找出删除的文件（数据库中有但目录中没有）
        deleted_files = db_files - current_files
        
        # 找出新增的文件（目录中有但数据库中没有）
        new_files = current_files - db_files
        
        # 找出可能更新的文件（比较大小和修改时间）
        updated_files = []
        common_files = db_files & current_files
        
        for file_path in common_files:
            try:
                # 获取当前文件信息
                current_attr = self.get_file_attributes(file_path, recalculate_hash=recalculate_hash)
                
                # 获取数据库中的文件信息
                self.cursor.execute(
                    "SELECT file_size, modified_time, file_hash FROM file_features WHERE file_path = ?",
                    (file_path,)
                )
                db_info = self.cursor.fetchone()
                
                if db_info and current_attr:
                    # 检查是否有更新
                    if not recalculate_hash:
                        # 如果不需要重新计算哈希值，只比较文件大小和修改时间
                        hash_changed = False
                    else:
                        hash_changed = (db_info[2] != current_attr['file_hash'])
                        
                    if (db_info[0] != current_attr['file_size'] or 
                        db_info[1] != current_attr['modified_time'] or 
                        hash_changed):
                        updated_files.append(file_path)
            except Exception as e:
                print(f"比较文件时出错 {file_path}: {e}")
        
        return {
            'deleted': list(deleted_files),
            'new': list(new_files),
            'updated': updated_files
        }
    
    def update_database(self, directory_path):
        """更新数据库以匹配当前目录状态"""
        # 首先删除数据库中已不存在的文件
        comparison = self.compare_with_database(directory_path, recalculate_hash=False)
        
        # 删除已不存在的文件记录
        for deleted_file in comparison['deleted']:
            try:
                self.cursor.execute("DELETE FROM file_features WHERE file_path = ?", (deleted_file,))
            except sqlite3.Error as e:
                print(f"删除文件记录错误 {deleted_file}: {e}")
        
        # 处理新增和更新的文件
        files_to_update = comparison['new'] + comparison['updated']
        batch_size = 1000  # 每批处理的文件数
        attributes_batch = []
        processed_count = 0
        
        print("正在更新数据库...")
        
        for file_path in files_to_update:
            try:
                attributes = self.get_file_attributes(file_path, recalculate_hash=True)
                if attributes:
                    attributes_batch.append(attributes)
                    processed_count += 1
                    
                    # 当批次满时，批量插入
                    if processed_count % batch_size == 0:
                        self.batch_save_file_attributes(attributes_batch, show_ditail=False)
                        attributes_batch = []
                        # 显示进度
                        print(f"已更新 {processed_count}/{len(files_to_update)} 个文件的属性")                        
            except Exception as e:
                print(f"更新文件记录错误 {file_path}: {e}")
        
        # 处理剩余的文件
        if attributes_batch:
            self.batch_save_file_attributes(attributes_batch, show_ditail=False)
            attributes_batch = []
            # 显示进度
            print(f"已更新 {processed_count}/{len(files_to_update)} 个文件的属性")                        
        
        self.conn.commit()
        print(f"数据库更新完成，删除了 {len(comparison['deleted'])} 个文件记录，更新了 {processed_count} 个文件记录。")
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.rw_reg_handlers.unregister_file_handler()
            self.conn.close()
            self.conn = None
            self.cursor = None
            
    def export_duplicates_to_json(self, json_file_path):
        """
        将所有重复的文件导出到指定的JSON文件
        
        参数:
            json_file_path: JSON输出文件的路径
        
        返回:
            bool: 导出是否成功
        """
        try:
            # 获取重复文件信息
            duplicates = self.find_duplicate_files()
            
            # 构建JSON输出格式
            output_data = {
                "export_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "duplicate_groups": duplicates,
                "total_groups": len(duplicates)
            }
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(os.path.abspath(json_file_path)), exist_ok=True)
            
            # 写入JSON文件
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功将 {len(duplicates)} 组重复文件导出到 {json_file_path}")
            return True
        except Exception as e:
            print(f"导出重复文件到JSON时出错: {e}")
            return False

    def handle_file(self, file_path,mode='r',data=None):
        """处理文件"""
        handled = self.rw_reg_handlers.handle_file(file_path,mode,data)
        if handled:
            return handled[0], handled[1]
        return None, None

    def thread_calc_files_hash(self,recalc_queue,result_queue,total_files=0):
        """
        多线程计算文件哈希值
        参数:
            recalc_queue: 包含需要计算哈希值的文件路径的队列
            result_queue: 用于存储计算结果的队列
            total_files: 总文件数，用于进度条显示
        """
        prograss=ProgressBar(total_files)
        
        def calc_file_hash(recalc_queue,result_queue):
            while True:
                file_path=recalc_queue.get()
                if file_path is None:
                    break
                fhash=self.calculate_file_hash(file_path)
                result_queue.put((file_path,fhash))
                recalc_queue.task_done()
                prograss.update()
        
        threads=[]
        for _ in range(self.max_threads):
            thread = threading.Thread(target=calc_file_hash, args=(recalc_queue,result_queue))
            threads.append(thread)
            thread.start()
        
        for _ in range(self.max_threads+1):
            recalc_queue.put(None)
            
        for t in threads:
            t.join()
        prograss.finish()

    def only_search_changed_files(self, directory_path):
        """
        搜索目录中与数据库中文件特征不一致的文件
        
        参数:
            directory_path: 要搜索的目录路径
        返回:
            list: 发生变化的文件列表
        """
        # 获取数据库中所有文件路径和完整属性
        self.cursor.execute("SELECT file_path, modified_time, file_size, file_hash FROM file_features")
        db_files = {row[0]: {'modified_time': row[1], 'file_size': row[2], 'file_hash': row[3]} for row in self.cursor.fetchall()}
        
        # 扫描目录中的文件
        current_files = set()
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and not os.path.islink(file_path):
                    # 规范化文件路径，确保与数据库中的路径格式一致
                    normalized_path = os.path.normpath(file_path)
                    current_files.add(normalized_path)
                
        # 转换为集合以确保正确的集合操作
        db_files_set = set(db_files.keys())
        
        # 计算新增文件和删除文件
        new_files = current_files - db_files_set
        delete_files = db_files_set - current_files
        
        # 计算存在于数据库和当前目录中的文件
        db_exist_files = current_files & db_files_set
        changed_files = []
        
        # 对比数据库中的文件，找出当前目录中与数据库中文件特征不一致的文件
        for file_path in db_exist_files:
            db_file_attr = db_files[file_path]
            current_file_attr = self.get_file_attributes(file_path, recalculate_hash=False)
            
            if current_file_attr and (
                current_file_attr['modified_time'] > db_file_attr['modified_time'] or \
                current_file_attr['file_size'] != db_file_attr['file_size']
            ):
                changed_files.append(file_path)
                
        # 计算文件哈希值
        result_queue = queue.Queue()
        # 创建一个新的队列并填充文件路径
        hash_queue = queue.Queue()
        for file_path in changed_files:
            hash_queue.put(file_path)
        
        self.thread_calc_files_hash(hash_queue, result_queue)
        changed_files = []
        while not result_queue.empty():
            file_path, fhash = result_queue.get()
            # 比较新计算的哈希值与数据库中存储的哈希值
            if fhash != db_files[file_path]['file_hash']:
                changed_files.append(file_path)
                
        return changed_files+list(new_files)+list(delete_files)

    def remove_file_from_database(self, file_path):
        """
        从数据库中删除指定文件的记录
        
        参数:
            file_path: 要从数据库中删除的文件路径
        
        返回:
            bool: 删除是否成功
        """
        try:
            # 规范化文件路径，确保与数据库中的路径格式一致
            normalized_path = os.path.normpath(file_path)
            
            # 执行删除操作
            self.cursor.execute("DELETE FROM file_features WHERE file_path = ?", (normalized_path,))
            self.conn.commit()
            
            # 检查是否有记录被删除
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"从数据库中删除文件记录错误 {file_path}: {e}")
            self.conn.rollback()
            return False

def add_args(parser,dir=None):
    """添加命令行参数"""
    # if dir is None:
    #     parser.add_argument('directory', help='要扫描的目录路径')
    # else:
    #     parser.add_argument('directory', default=dir, help='要扫描的目录路径')
    parser.add_argument('--db', default=FILE_FEATURES_DB_FILENAME, help='数据库文件路径')
    parser.add_argument('--find-duplicates', action='store_true', help='仅查找重复文件')
    parser.add_argument('--compare', action='store_true', help='比较目录与数据库')
    parser.add_argument('--chenged', action='store_true', help='搜索目录中发生变化的文件')    
    parser.add_argument('--update', action='store_true', help='更新数据库')
    parser.add_argument('--read-file', help='读取指定文件的内容')
    parser.add_argument('--threads', type=int, default=4, help='哈希计算的最大线程数（默认：4）')
    parser.add_argument('--hash-algorithm', default='md5', choices=['md5', 'sha1', 'sha256'], 
                        help='哈希计算算法（默认：md5）')
    parser.add_argument('--force-recalculate', action='store_true', help='强制重新计算所有文件的哈希值')
    parser.add_argument('--export-duplicates', default=FILE_DUMP_FILENAME, help='将重复文件导出到指定的JSON文件')
    parser.add_argument('--no-find-duplicates', action='store_true', help='扫描后不自动查找重复文件（默认会自动查找）')
            
def main(args: argparse.Namespace):
    """主函数"""
      
    # 确保目录路径是绝对路径
    directory_path = os.path.abspath(args.directory)
    #获取windows系统下的真实路径
    if os.name == 'nt':
        directory_path = os.path.realpath(directory_path)
    if not os.path.isdir(directory_path):
        print(f"错误: 目录 '{directory_path}' 不存在。")
        return
    # 确保数据库文件路径是绝对路径
    db_path = os.path.join(directory_path,args.db)
    json_file_path = os.path.join(directory_path,args.export_duplicates)
    
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)
    if not os.path.isabs(json_file_path):
        json_file_path = os.path.abspath(json_file_path)
    
    # 初始化文件重复查找器
    finder = FileDuplicateFinder(
        db_path=db_path, 
        max_threads=args.threads, 
        hash_algorithm=args.hash_algorithm,
        force_recalculate=args.force_recalculate
    )
    
    try:
        # 读取文件内容操作
        if args.read_file:
            file_path = os.path.abspath(args.read_file)
            file_type, handled = finder.handle_file(file_path,'r',None)
            if file_type == 'text' and handled:
                print(f"\n文件内容: {file_path}\n{'-' * 50}\n{handled}\n{'-' * 50}")
            return
            
        # 检查数据库是否存在
        db_exists = os.path.exists(db_path)
        
        # 导出重复文件到JSON
        if args.export_duplicates!=FILE_DUMP_FILENAME:
            if not db_exists:
                print(f"错误: 数据库文件 '{db_path}' 不存在，请先扫描目录创建数据库。")
                return
            
            print("正在查找重复文件...")
            
            finder.export_duplicates_to_json(json_file_path)
            return
        
        if args.chenged:
            # 仅搜索目录中发生变化的文件
            if not db_exists:
                print(f"错误: 数据库文件 '{db_path}' 不存在，请先扫描目录创建数据库。")
                return
                            
            changed_files=finder.only_search_changed_files(directory_path)
            if not changed_files:
                print("未找到发生变化的文件。")
            else:
                print(f"找到 {len(changed_files)} 个发生变化的文件:\n")
                for file_path in changed_files:  
                    print(f"  - {file_path}")
            return
        
        if args.find_duplicates:
            # 仅查找重复文件
            print("正在查找重复文件...")
            duplicates = finder.find_duplicate_files()
            
            if not duplicates:
                print("未找到重复文件。")
            else:
                print(f"找到 {len(duplicates)} 组重复文件:\n")
                for i, group in enumerate(duplicates, 1):
                    print(f"组 {i}: 哈希值 {group['hash']}")
                    for file_info in group['files']:
                        print(f"  - {file_info['path']}")
                        print(f"    大小: {file_info['size']} 字节")
                        print(f"    创建时间: {file_info['created']}")
                        print(f"    修改时间: {file_info['modified']}")
                        print(f"    所有者: {file_info['owner']}")
                    print()
 
                finder.export_duplicates_to_json(json_file_path)
        elif args.compare:
            # 比较目录与数据库
            if not db_exists:
                print(f"错误: 数据库文件 '{args.db}' 不存在，请先扫描目录创建数据库。")
                return
                
            print(f"正在比较目录 '{directory_path}' 与数据库...")
            changes = finder.compare_with_database(directory_path)
            
            print(f"\n目录变更分析结果:\n{'-' * 50}")
            
            if changes['deleted']:
                print(f"删除的文件 ({len(changes['deleted'])}):")
                for file_path in changes['deleted'][:5]:  # 只显示前5个
                    print(f"  - {file_path}")
                if len(changes['deleted']) > 5:
                    print(f"  ... 还有 {len(changes['deleted']) - 5} 个文件")
            else:
                print("没有删除的文件。")
                
            if changes['new']:
                print(f"\n新增的文件 ({len(changes['new'])}):")
                for file_path in changes['new'][:5]:  # 只显示前5个
                    print(f"  - {file_path}")
                if len(changes['new']) > 5:
                    print(f"  ... 还有 {len(changes['new']) - 5} 个文件")
            else:
                print("没有新增的文件。")
                
            if changes['updated']:
                print(f"\n更新的文件 ({len(changes['updated'])}):")
                for file_path in changes['updated'][:5]:  # 只显示前5个
                    print(f"  - {file_path}")
                if len(changes['updated']) > 5:
                    print(f"  ... 还有 {len(changes['updated']) - 5} 个文件")
            else:
                print("没有更新的文件。")
                
            # 询问是否更新数据库
            if changes['deleted'] or changes['new'] or changes['updated']:
                update = input("\n是否要根据目录文件更新数据库？(y/n): ").lower()
                if update == 'y':
                    finder.update_database(directory_path)
 
                    finder.export_duplicates_to_json(json_file_path)
        elif args.update:
            # 更新数据库
            if not db_exists:
                print(f"错误: 数据库文件 '{args.db}' 不存在，请先扫描目录创建数据库。")
                return
                
            print(f"正在更新数据库以匹配目录 '{directory_path}'...")
            finder.update_database(directory_path)
                       
            finder.export_duplicates_to_json(json_file_path)
        else:
            # 默认行为：扫描目录
            print(f"正在扫描目录 '{directory_path}' 及其子目录...")
            finder.scan_directory(directory_path)
            
            # 根据命令行选项决定是否查找重复文件，默认查找
            if not args.no_find_duplicates:
                duplicates = finder.find_duplicate_files()
                
                if not duplicates:
                    print("未找到重复文件。")
                else:
                    print(f"找到 {len(duplicates)} 组重复文件:\n")
                    for i, group in enumerate(duplicates, 1):
                        print(f"组 {i}: 哈希值 {group['hash']}")
                        for file_info in group['files'][:3]:  # 每个组只显示前3个文件
                            print(f"  - {file_info['path']}")
                            print(f"    大小: {file_info['size']} 字节")
                            print(f"    修改时间: {file_info['modified']}")
                        if len(group['files']) > 3:
                            print(f"  ... 还有 {len(group['files']) - 3} 个文件")
                        print()
                        
                    finder.export_duplicates_to_json(json_file_path)
    finally:
        finder.close()
        


if __name__ == "__main__":
    main()