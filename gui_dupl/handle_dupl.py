import sys
import os
# sys.path.insert(0, os.path.abspath(
#     os.path.join(os.path.dirname(__file__), '..',"filedup")))   # 把 repo/ 塞进 path

import json
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem, 
    QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, 
    QGroupBox, QLabel, QMessageBox, QFileDialog, QCheckBox, QGridLayout,
    QFrame, QScrollArea, QSizePolicy,QMenu
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QImage, QPixmap
from filedup.rw_reg_handlers import RWRegHandlers
import base64

# 添加发送到回收站功能
try:
    import winshell
    HAS_WINSHELL = True
except ImportError:
    HAS_WINSHELL = False
    print("警告: 未安装winshell库，回收站功能可能不可用")

class DuplicateFileHandler(QMainWindow):
    def __init__(self):
        super().__init__()
        # 存储当前显示的图片，用于窗口大小变化时重新缩放
        self.current_pixmap = None
        self.init_ui()
        self.duplicate_groups = []
        self.selected_files = set()  # 存储选中的文件路径
        self.rw_reg_handlers = RWRegHandlers()
        self.dest_dir = None
    
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('重复文件处理工具')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单
        self.create_menus()
        
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 创建文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(['文件名', '大小', '修改时间', '创建时间', '所有者'])
        self.file_tree.setColumnWidth(0, 400)  # 设置第一列宽度
        self.file_tree.setColumnWidth(1, 80)
        self.file_tree.setColumnWidth(2, 150)
        self.file_tree.setColumnWidth(3, 150)
        self.file_tree.setColumnWidth(4, 100)
        self.file_tree.itemClicked.connect(self.on_file_clicked)
        # 设置右键菜单
        self.file_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.on_context_menu)
        
        # 创建快速选择和过滤区域
        action_group = QGroupBox("操作选项")
        action_layout = QGridLayout(action_group)
        
        # 快速选择按钮
        self.select_oldest_btn = QPushButton("选中最早的文件")
        self.select_oldest_btn.clicked.connect(self.select_oldest_files)
        self.select_newest_btn = QPushButton("选中最晚的文件")
        self.select_newest_btn.clicked.connect(self.select_newest_files)
        self.invert_selection_btn = QPushButton("反选")
        self.invert_selection_btn.clicked.connect(self.invert_selection)
        self.clear_selection_btn = QPushButton("取消选择")
        self.clear_selection_btn.clicked.connect(self.clear_selection)
        
        # 过滤输入框
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("输入过滤关键字...")
        self.filter_edit.textChanged.connect(self.filter_files)
        
        # 添加到布局
        action_layout.addWidget(QLabel("快速选择:"), 0, 0)
        action_layout.addWidget(self.select_oldest_btn, 0, 1)
        action_layout.addWidget(self.select_newest_btn, 0, 2)
        action_layout.addWidget(self.invert_selection_btn, 0, 3)
        action_layout.addWidget(self.clear_selection_btn, 0, 4)
        action_layout.addWidget(QLabel("过滤:"), 1, 0)
        action_layout.addWidget(self.filter_edit, 1, 1, 1, 4)
        
        # 创建操作按钮区域
        btn_group = QGroupBox("文件操作")
        btn_layout = QHBoxLayout(btn_group)
        
        self.delete_btn = QPushButton("移动到回收站")
        self.delete_btn.clicked.connect(self.move_to_recycle_bin)
        self.move_btn = QPushButton("移动到指定目录")
        self.move_btn.clicked.connect(self.move_to_directory)
        self.copy_btn = QPushButton("复制到指定目录")
        self.copy_btn.clicked.connect(self.copy_to_directory)
        
        # 添加按钮到布局
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.move_btn)
        btn_layout.addWidget(self.copy_btn)
        
        # 添加所有组件到左侧布局
        left_layout.addWidget(QLabel("重复文件列表:"))
        left_layout.addWidget(self.file_tree)
        left_layout.addWidget(action_group)
        left_layout.addWidget(btn_group)
        
        # 创建右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 创建文件查看选项
        view_options = QGroupBox("查看选项")
        view_layout = QHBoxLayout(view_options)
        
        self.view_content_check = QCheckBox("显示文件内容")
        self.view_content_check.setChecked(True)
        self.view_content_check.stateChanged.connect(self.on_file_clicked)
        
        view_layout.addWidget(self.view_content_check)
        
        # 创建内容显示区域容器
        self.content_container = QWidget()
        self.content_container_layout = QVBoxLayout(self.content_container)
        
        # 创建文件内容显示区域 - QTextEdit
        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setFont(QFont("Consolas", 10))
        
        # 创建图片显示区域 - QLabel + QScrollArea
        self.image_scroll_area = QScrollArea()
        self.image_scroll_area.setWidgetResizable(True)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.image_scroll_area.setWidget(self.image_label)
        
        # 初始状态下，只显示QTextEdit
        self.image_scroll_area.hide()
        
        # 添加到内容容器
        self.content_container_layout.addWidget(self.content_view)
        self.content_container_layout.addWidget(self.image_scroll_area)
        
        # 添加到右侧布局
        right_layout.addWidget(view_options)
        right_layout.addWidget(self.content_container)
        
        # 添加面板到分割器
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        
        # 设置分割器比例
        main_splitter.setSizes([700, 500])
        
        # 设置中心部件
        self.setCentralWidget(main_splitter)
        
        # 添加状态栏
        self.statusBar().showMessage('就绪')

    def set_dest_dir(self, dest_dir):
        self.dest_dir = dest_dir
           
    def create_menus(self):
        """创建菜单"""
        # 获取菜单栏
        menubar = self.menuBar()
        
        # 创建文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 创建打开动作
        open_action = file_menu.addAction('打开')
        open_action.triggered.connect(self.load_duplicate_file)
        
        # 创建退出动作
        exit_action = file_menu.addAction('退出')
        exit_action.triggered.connect(self.close_window)
    
    #注册window事件
    def closeEvent(self, event):
        """关闭窗口时注销文件处理器"""
        self.rw_reg_handlers.unregister_file_handler()
        event.accept()
        
    def close_window(self):
        """关闭窗口"""
        # self.rw_reg_handlers.unregister_file_handler()
        self.close()
    
    def load_duplicate_file(self):
        """通过菜单打开JSON文件"""
        
        json_path, _ = QFileDialog.getOpenFileName(
            self, "选择重复文件JSON", self.dest_dir, "JSON Files (*.json);;All Files (*)")
            
        if json_path:
            try:
                self.dest_dir = os.path.dirname(json_path)
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.duplicate_groups = data.get('duplicate_groups', [])
                    self.populate_file_tree()
                    self.statusBar().showMessage(f'已加载 {len(self.duplicate_groups)} 组重复文件')
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")
    
    def populate_file_tree(self):
        """填充文件树"""
        self.file_tree.clear()
        self.selected_files.clear()
        
        for group_idx, group in enumerate(self.duplicate_groups):
            hash_value = group.get('hash', 'Unknown')
            group_item = QTreeWidgetItem([f"组 {group_idx+1}: {hash_value}", "", "", "", ""])
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            
            # 设置组项目的背景色
            group_item.setBackground(0, QColor(240, 240, 240))
            
            files = group.get('files', [])
            for file_info in files:
                file_path = file_info.get('path', '')
                file_name = os.path.basename(file_path)
                file_size = self.format_size(file_info.get('size', 0))
                
                # 格式化时间
                modified_time = self.format_time(file_info.get('modified', ''))
                created_time = self.format_time(file_info.get('created', ''))
                owner = file_info.get('owner', '')
                
                file_item = QTreeWidgetItem([file_name, file_size, modified_time, created_time, owner])
                file_item.setData(0, Qt.UserRole, file_path)  # 存储完整路径
                file_item.setCheckState(0, Qt.Unchecked)  # 添加复选框
                
                group_item.addChild(file_item)
            
            self.file_tree.addTopLevelItem(group_item)
            group_item.setExpanded(True)
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def format_time(self, time_str):
        """格式化时间字符串"""
        if not time_str:
            return ""
        
        try:
            # 尝试不同的时间格式
            if 'T' in time_str:
                # ISO格式: 2020-12-09T12:06:17.370000
                if '.' in time_str:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(time_str)
            else:
                # 其他格式
                dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return time_str  # 如果解析失败，返回原始字符串
    
    def on_context_menu(self, position):
        """显示右键菜单"""
        # 获取右键点击位置的项目
        item = self.file_tree.itemAt(position)
        if not item:  # 如果没有点击任何项目，不显示菜单
            return
            
        file_path = item.data(0, Qt.UserRole)
        if not file_path or not os.path.exists(file_path):  # 如果没有有效的文件路径，不显示菜单
            return
            
        # 创建右键菜单
        context_menu = QMenu()
        
        # 添加菜单项
        open_explorer_action = context_menu.addAction("在资源管理器中打开文件所在目录")
        open_explorer_action.triggered.connect(lambda: self.open_file_in_explorer(file_path))
        
        open_cmd_action = context_menu.addAction("在文件所在目录打开命令行")
        open_cmd_action.triggered.connect(lambda: self.open_cmd_in_directory(file_path))
        
        # 在右键点击位置显示菜单
        context_menu.exec_(self.file_tree.viewport().mapToGlobal(position))
        
    def open_file_in_explorer(self, file_path):
        """在资源管理器中打开文件所在目录"""
        directory = os.path.dirname(file_path)
        if os.path.exists(directory):
            # 在Windows系统上打开资源管理器
            os.startfile(directory)
    
    def open_cmd_in_directory(self, file_path):
        """在文件所在目录打开命令行"""
        directory = os.path.dirname(file_path)
        if os.path.exists(directory):
            # 在Windows系统上打开命令提示符
            os.system(f'start cmd.exe /K cd /d "{directory}"')
            
    def on_file_clicked(self):
        """当文件项被点击时"""
        selected_items = self.file_tree.selectedItems()
        if not selected_items or not self.view_content_check.isChecked():
            return
        
        item = selected_items[0]
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.display_file_content(file_path)
    
    def resizeEvent(self, event):
        # 窗口大小变化时，重新缩放图片以保持纵横比例
        super().resizeEvent(event)
        if self.current_pixmap and hasattr(self, 'image_label'):
            self.image_label.setPixmap(self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
            
    def display_file_content(self, file_path):
        """显示文件内容"""
        
        try:
            # 读取文件内容
            file_type, content=self.rw_reg_handlers.handle_file(file_path, mode='r', data=None)
            
            # 确保两个控件都显示，后面再根据需要隐藏
            self.content_view.show()
            self.image_scroll_area.hide()
            
            if file_type == 'text' and content:
                self.content_view.setText(content)
                self.content_view.show()
                self.image_scroll_area.hide()
                return
            elif file_type == 'img' and content:
                # 使用QImage控件显示图片
                self.content_view.hide()
                self.image_scroll_area.show()
                
                # 加载图片数据（先对base64编码的content进行解码）
                image = QImage()
                try:
                    decoded_data = base64.b64decode(content)
                    image.loadFromData(decoded_data)
                except Exception as e:
                    print(f"图片解码或加载失败: {e}")
                
                if not image.isNull():
                    # 创建QPixmap并设置给QLabel
                    pixmap = QPixmap.fromImage(image)
                    
                    # 保持图片的纵横比例
                    self.image_label.setScaledContents(False)
                    
                    # 保存当前pixmap，用于窗口大小变化时重新缩放
                    self.current_pixmap = pixmap
                    
                    # 设置图片，并保持纵横比例
                    self.image_label.setPixmap(pixmap.scaled(
                        self.image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    ))
                    
                    # 调整滚动区域
                    self.image_scroll_area.setWidgetResizable(True)
                else:
                    self.image_label.setText("无法加载图片")
                return
            elif file_type == 'audio' and content:
                self.content_view.setHtml(f"<audio controls><source src='data:audio/mp3;base64,{content}' type='audio/mp3'></audio>")
                self.content_view.show()
                self.image_scroll_area.hide()
                return
            elif file_type == 'video' and content:
                self.content_view.setHtml(f"<video controls><source src='data:video/mp4;base64,{content}' type='video/mp4'></video>")
                self.content_view.show()
                self.image_scroll_area.hide()
                return
            else:
                self.content_view.setText("文件内容为空")
                self.content_view.show()
                self.image_scroll_area.hide()
        except Exception as e:
            self.content_view.setText(f"读取文件失败: {str(e)}")
            self.content_view.show()
            self.image_scroll_area.hide()
    
    def select_oldest_files(self):
        """选中每组中最早的文件"""
        self.clear_selection()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            oldest_time = None
            oldest_item = None
            
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                file_path = file_item.data(0, Qt.UserRole)
                
                # 获取修改时间
                modified_str = file_item.text(2)
                try:
                    modified_time = datetime.strptime(modified_str, '%Y-%m-%d %H:%M:%S')
                    
                    if oldest_time is None or modified_time < oldest_time:
                        oldest_time = modified_time
                        oldest_item = file_item
                except:
                    continue
            
            if oldest_item:
                oldest_item.setCheckState(0, Qt.Checked)
                self.selected_files.add(oldest_item.data(0, Qt.UserRole))
    
    def select_newest_files(self):
        """选中每组中最晚的文件"""
        self.clear_selection()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            newest_time = None
            newest_item = None
            
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                file_path = file_item.data(0, Qt.UserRole)
                
                # 获取修改时间
                modified_str = file_item.text(2)
                try:
                    modified_time = datetime.strptime(modified_str, '%Y-%m-%d %H:%M:%S')
                    
                    if newest_time is None or modified_time > newest_time:
                        newest_time = modified_time
                        newest_item = file_item
                except:
                    continue
            
            if newest_item:
                newest_item.setCheckState(0, Qt.Checked)
                self.selected_files.add(newest_item.data(0, Qt.UserRole))
    
    def clear_selection(self):
        """清除所有选择"""
        self.selected_files.clear()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                file_item.setCheckState(0, Qt.Unchecked)
                
    def invert_selection(self):
        """反选所有文件"""
        new_selected_files = set()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                file_path = file_item.data(0, Qt.UserRole)
                
                # 反转选中状态
                if file_item.checkState(0) == Qt.Checked:
                    file_item.setCheckState(0, Qt.Unchecked)
                else:
                    file_item.setCheckState(0, Qt.Checked)
                    new_selected_files.add(file_path)
        
        # 更新选中文件集合
        self.selected_files = new_selected_files
    
    def filter_files(self):
        """根据输入过滤文件"""
        keyword = self.filter_edit.text().lower()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            group_visible = False
            
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                file_path = file_item.data(0, Qt.UserRole).lower()
                file_name = file_item.text(0).lower()
                
                # 检查文件名或路径是否包含关键字
                match = keyword in file_path or keyword in file_name
                file_item.setHidden(not match)
                
                if match:
                    group_visible = True
            
            # 如果组内有可见的文件，则显示组
            group_item.setHidden(not group_visible)
    
    def move_to_recycle_bin(self):
        """将选中的文件移动到回收站"""
        if not HAS_WINSHELL:
            QMessageBox.warning(self, "警告", "未安装winshell库，无法使用回收站功能")
            return
        
        if not self.get_selected_files():
            QMessageBox.information(self, "提示", "请先选择要移动的文件")
            return
        
        reply = QMessageBox.question(
            self, "确认", f"确定要将选中的 {len(self.selected_files)} 个文件移到回收站吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            
            for file_path in list(self.selected_files):
                try:
                    winshell.delete_file(file_path)
                    success_count += 1
                    # 从列表中移除已删除的文件
                    self.remove_file_from_tree(file_path)
                except Exception as e:
                    fail_count += 1
                    print(f"删除文件失败: {file_path}, 错误: {str(e)}")
            
            QMessageBox.information(
                self, "结果", f"操作完成: 成功删除 {success_count} 个文件, 失败 {fail_count} 个文件"
            )
    
    def move_to_directory(self):
        """将选中的文件移动到指定目录"""
        if not self.get_selected_files():
            QMessageBox.information(self, "提示", "请先选择要移动的文件")
            return
        
        target_dir = QFileDialog.getExistingDirectory(
            self, "选择目标目录", "", QFileDialog.ShowDirsOnly
        )
        
        if target_dir:
            reply = QMessageBox.question(
                self, "确认", f"确定要将选中的 {len(self.selected_files)} 个文件移动到 {target_dir} 吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.perform_file_operation(target_dir, shutil.move)
    
    def copy_to_directory(self):
        """将选中的文件复制到指定目录"""
        if not self.get_selected_files():
            QMessageBox.information(self, "提示", "请先选择要复制的文件")
            return
        
        target_dir = QFileDialog.getExistingDirectory(
            self, "选择目标目录", "", QFileDialog.ShowDirsOnly
        )
        
        if target_dir:
            reply = QMessageBox.question(
                self, "确认", f"确定要将选中的 {len(self.selected_files)} 个文件复制到 {target_dir} 吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.perform_file_operation(target_dir, shutil.copy2)
    
    def perform_file_operation(self, target_dir, operation_func):
        """执行文件操作（移动或复制）"""
        success_count = 0
        fail_count = 0
        
        for file_path in list(self.selected_files):
            try:
                file_name = os.path.basename(file_path)
                target_path = os.path.join(target_dir, file_name)
                
                # 处理文件名冲突
                counter = 1
                while os.path.exists(target_path):
                    name, ext = os.path.splitext(file_name)
                    target_path = os.path.join(target_dir, f"{name}_{counter}{ext}")
                    counter += 1
                
                operation_func(file_path, target_path)
                success_count += 1
                
                # 如果是移动操作，从树中移除文件
                if operation_func == shutil.move:
                    self.remove_file_from_tree(file_path)
            except Exception as e:
                fail_count += 1
                print(f"操作失败: {file_path}, 错误: {str(e)}")
        
        operation_name = "移动" if operation_func == shutil.move else "复制"
        QMessageBox.information(
            self, "结果", f"{operation_name}完成: 成功 {success_count} 个文件, 失败 {fail_count} 个文件"
        )
    
    def get_selected_files(self):
        """获取所有选中的文件"""
        self.selected_files.clear()
        
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                if file_item.checkState(0) == Qt.Checked:
                    file_path = file_item.data(0, Qt.UserRole)
                    self.selected_files.add(file_path)
        
        return self.selected_files
    
    def remove_file_from_tree(self, file_path):
        """从树中移除指定文件"""
        for group_idx in range(self.file_tree.topLevelItemCount()):
            group_item = self.file_tree.topLevelItem(group_idx)
            for file_idx in range(group_item.childCount()):
                file_item = group_item.child(file_idx)
                if file_item.data(0, Qt.UserRole) == file_path:
                    group_item.takeChild(file_idx)
                    self.selected_files.discard(file_path)
                    # 如果组内没有文件了，移除组
                    if group_item.childCount() == 0:
                        self.file_tree.takeTopLevelItem(group_idx)
                    return



def main(dir=None):
    """主函数"""
    app = QApplication(sys.argv)
    window = DuplicateFileHandler()
    if dir:
        window.set_dest_dir(dir)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()