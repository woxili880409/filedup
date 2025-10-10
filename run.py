import sys
from filedup.file_duplicate_finder import main as filedup_main
from filedup.global_vars import log_print
from gui_dupl.handle_dupl import main as gui_main
import argparse

def main():
    """主函数"""
    # 创建一个只解析--gui参数的解析器
    parser = argparse.ArgumentParser(description='文件重复查找工具', add_help=False)
    parser.add_argument('-g', '--gui', action='store_true', help='使用图形界面')
    
    # 使用parse_known_args解析参数，这样可以只解析--gui参数，保留其他参数
    args, remaining_args = parser.parse_known_args()
    
    if args.gui:
        # 图形界面模式，只需要目录参数
        if remaining_args:
            # 如果有剩余参数，第一个参数作为目录
            gui_main(remaining_args[0])
        else:
            log_print("请指定目录或使用图形界面")
            parser.print_help()
            sys.exit(1)
    else:
        # 命令行模式，将所有剩余参数传递给file_duplicate_finder的main函数
        # 由于file_duplicate_finder的main函数会重新解析命令行参数
        # 我们需要修改sys.argv，然后调用其main函数
        original_argv = sys.argv.copy()
        try:
            # 设置sys.argv为[script_name] + remaining_args
            sys.argv = [original_argv[0]] + remaining_args
            
            # 调用file_duplicate_finder的main函数，不传递dir参数
            # 这样它会自己从sys.argv中解析所有参数
            filedup_main()
        except SystemExit:
            # 捕获sys.exit()调用，以避免程序过早退出
            pass
        finally:
            # 恢复原始的sys.argv
            sys.argv = original_argv

if __name__ == '__main__':
    main()
