import sys
from filedup.file_duplicate_finder import main as filedup_main,add_args as filedup_add_args
from filedup.global_vars import log_print,LOG_LEVEL_ERROR
from gui_dupl.handle_dupl import main as gui_main,add_args as gui_add_args
import argparse

def main():
    """主函数"""
    # 创建一个只解析--gui参数的解析器
    parser = argparse.ArgumentParser(description='文件重复查找工具', add_help=False)
    subparsers = parser.add_subparsers(dest='command')
    parser_dupl = subparsers.add_parser('dupl', help='查找重复文件')
    filedup_add_args(parser_dupl)
    parser_gui = subparsers.add_parser('gui', help='使用图形界面')
    gui_add_args(parser_gui)
    parser.add_argument('directory', type=str, help='要查找重复文件的目录')
    
    try:   
        args = parser.parse_args()
        print(args)
    except argparse.ArgumentError as e:
        log_print(f"参数错误: {e}",log_level=LOG_LEVEL_ERROR)
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'dupl':
        filedup_main(args)
    elif args.command == 'gui':
        gui_main(args)
    else:
        log_print("请指定命令（dupl或gui）")
        parser.print_help()
        sys.exit(1)
if __name__ == '__main__':
    main()
