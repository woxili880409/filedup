import sys
from filedup.file_duplicate_finder import main as filedup_main
from filedup.global_vars import log_print
from gui_dupl.handle_dupl import main as gui_main
import argparse

def add_args(parser):
    parser.add_argument('dir', default=None, help='指定要查找重复文件的目录')
    parser.add_argument('-g', '--gui', action='store_true', help='使用图形界面')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='文件重复查找工具')
    add_args(parser)
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as e:
        log_print(f"参数错误: {e}")
        sys.exit(1)
        
    if args.gui:
        gui_main(args.dir)
    elif args.dir:
        filedup_main(args.dir)
    else:
        log_print("请指定目录或使用图形界面")
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
