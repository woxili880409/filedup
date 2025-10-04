import subprocess
import sys
import os

print("验证UTF-8编码修复是否有效...")

# 确保工作目录正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 运行修改后的test_finder.py
proc = subprocess.Popen(
    [sys.executable, "test_finder.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding="utf-8",
    text=True
)

# 显示输出
stdout, stderr = proc.communicate()
print("标准输出:")
print(stdout)

if stderr:
    print("标准错误:")
    print(stderr)

print(f"退出码: {proc.returncode}")
print("\n验证完成。如果没有出现'Non-UTF-8 code'错误，则说明修复成功。")