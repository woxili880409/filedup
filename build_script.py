#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from PyInstaller.__main__ import run

# 执行pyinstaller命令
if __name__ == '__main__':
    # 定义打包参数
    args = [
        'run.py',
        '--name', 'filedup',
        '--onedir',  # 使用文件夹模式，这样会正确包含所有模块文件
        # 移除--noconsole选项，以便dupl子命令可以正常显示输出
        '--clean',
        '--add-data', 'filedup;filedup',
        '--add-data', 'gui_dupl;gui_dupl',
        '--add-data', 'reg_handlers.json;.',
        '--hidden-import', 'filedup',
        '--hidden-import', 'gui_dupl',
        '--hidden-import', 'filedup.file_duplicate_finder',
        '--hidden-import', 'filedup.global_vars',
        '--hidden-import', 'filedup.prograss',
        '--hidden-import', 'filedup.rw_video',
        '--hidden-import', 'filedup.rw_docx_wps',
        '--hidden-import', 'filedup.rw_img',
        '--hidden-import', 'filedup.rw_interface',
        '--hidden-import', 'filedup.rw_reg_handlers',
        '--hidden-import', 'gui_dupl.handle_dupl',
    ]
    
    print("开始打包...")
    print(f"执行命令: pyinstaller {' '.join(args)}")
    
    # 执行打包
    run(args)
    
    print("\n打包完成！请检查dist目录")
    print("注意：由于使用了--onedir选项，程序将被打包为文件夹形式")
    print("请运行 dist/filedup/filedup.exe 而不是 dist/filedup.exe")