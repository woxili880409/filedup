# File Duplicate Finder
# 文件重复查找器

An efficient file duplicate finder developed in Python, which can scan all files in a directory, generate file features and store them in a SQLite database, and then identify duplicate files based on hash values.

一个用Python开发的高效文件重复查找工具，可以扫描目录中的所有文件，生成文件特征并存储到SQLite数据库中，然后根据哈希值识别重复文件。

## 功能特点

1. **文件特征提取**：遍历指定目录及子目录，提取文件的创建时间、修改时间、所有者等属性，并为每个文件生成唯一的哈希值
Traverse the specified directory and its subdirectories, extract the creation time, modification time, owner, etc. of the files, and generate a unique hash value for each file.
2. **数据存储**：将文件特征保存到SQLite数据库中，便于后续查询和比较
Store the file features in a SQLite database for easy querying and comparison.
3. **重复文件识别**：根据文件哈希值快速识别重复文件，并显示详细特征信息
Identify duplicate files based on hash values quickly and display detailed feature information.
4. **变更检测**：支持与之前存储的数据对比，检测目录中的文件变更（新增、删除、更新）
Support comparing the directory with the previous data to detect changes (add, delete, update) in the files.
5. **数据更新**：可根据目录中的实际文件更新SQLite数据库
Update the SQLite database based on the actual files in the directory.
6. **文件内容查看**：提供接口查看指定文件的内容
Provide an interface to view the content of a specified file.
7. **JSON导出**：支持将重复文件信息导出为JSON格式文件，便于后续分析或与其他系统集成
Support exporting the duplicate file information in JSON format for analysis or integration with other systems.

## 系统要求

- Python 3.6 或更高版本
- 无需安装额外依赖库（使用Python标准库，包括sqlite3）

## 使用方法

### 基本扫描
在默认情况下，程序会自动查找重复文件并存储到数据库中。

其中数据库更新的策略是：
1. 如果文件哈希值不存在，则插入新记录
2. 如果文件哈希值已存在，且文件路径、大小、创建时间、修改时间、访问时间、所有者等6个属性都没有变化，则跳过更新
3. 如果文件哈希值已存且上述6个属性有变更，则检查文件大小或修改时间是否有变化，若有变化，则更新该记录

### 扫描目录并创建特征数据

扫描指定目录并创建文件特征数据，默认情况下会自动查找重复文件：

```bash
python file_duplicate_finder.py <目录路径>
```

例如：

```bash
python file_duplicate_finder.py D:\Documents
```

如需扫描后不自动查找重复文件，可以使用--no-find-duplicates选项：

```bash
python file_duplicate_finder.py <目录路径> --no-find-duplicates
```

### 查找重复文件

直接查找数据中的重复文件（需先进行扫描创建数据库）：

```bash
python file_duplicate_finder.py <目录路径> --find-duplicates
```

### 比较目录变更

比较当前目录与数据库中的记录，检测文件变化：

```bash
python file_duplicate_finder.py <目录路径> --compare
```

比较完成后，程序会询问是否根据实际文件更新数据库。

### 更新数据

直接更新数据库以匹配当前目录状态,注意，此操作重新计算所有文件的哈希值，而只是对比文件大小和修改时间：

- 如果文件大小和修改时间没有变化，则跳过更新
- 如果文件大小或修改时间有变化，则重新计算哈希值并则更新数据库
- 因此，此操作可能不能完全反映目录的实际情况，但可以快速找到目录中新增、删除或修改的文件，请谨慎使用。

```bash
python file_duplicate_finder.py <目录路径> --update
```

### 查看文件内容

读取并显示指定文件的内容：

- 程序默认可以读取文本文件（如.txt、.md、.py等）的前4KB内容
- 对于二进制文件，程序会以十六进制格式显示前4KB内容
- 对于无法访问的文件，程序会跳过并记录错误信息
- 程序提供接口，根据文件扩展名查看指定类型文件的内容，目前已经提供了word、wps文档的查看功能，但其是基于win32com库，在其他平台运行时会报错。
- 程序接口提供修改文件内容的功能，但从安全角度考虑，不建议直接修改文件内容。

```bash
python file_duplicate_finder.py <任意目录路径> --read-file <文件路径>
```

### 导出重复文件到JSON

将找到的重复文件信息导出为JSON格式文件：

```bash
python file_duplicate_finder.py <目录路径> --export-duplicates <输出JSON文件路径>
```

例如：

```bash
python file_duplicate_finder.py D:\Documents --export-duplicates duplicates.json
```

### 指定数据库文件

使用`--db`参数指定自定义数据库文件路径：

```bash
python file_duplicate_finder.py <目录路径> --db my_custom_data.db
```

## 命令行参数

以下是所有可用的命令行参数及其说明：

| 参数 | 类型 | 说明 |
|------|------|------|
| `<目录路径>` | 必填 | 要扫描的目录路径 |
| `--db <路径>` | 可选 | 数据库文件路径（默认：file_features.db） |
| `--find-duplicates` | 标志 | 仅查找重复文件（需先进行扫描创建数据库） |
| `--compare` | 标志 | 比较目录与数据库，检测文件变更 |
| `--update` | 标志 | 更新数据库以匹配当前目录状态 |
| `--read-file <文件路径>` | 可选 | 读取并显示指定文件的内容 |
| `--threads <数量>` | 可选 | 哈希计算的最大线程数（默认：4） |
| `--hash-algorithm <算法>` | 可选 | 哈希计算算法（md5、sha1、sha256，默认：md5） |
| `--force-recalculate` | 标志 | 强制重新计算所有文件的哈希值 |
| `--export-duplicates <JSON文件路径>` | 可选 | 将重复文件信息导出为JSON格式文件 |
| `--no-find-duplicates` | 标志 | 扫描后不自动查找重复文件（默认会自动查找） |

## 工作原理

1. **文件扫描**：使用`os.walk`遍历目录及其子目录中的所有文件
2. **哈希计算**：使用指定的哈希算法（默认：MD5）计算文件内容的哈希值，确保唯一性
3. **数据存储**：使用SQLite数据库存储文件路径、大小、时间戳、所有者和哈希值等信息
4. **重复检测**：通过分析找出具有相同哈希值的文件组
5. **变更比较**：对比当前目录文件与数据库记录，识别新增、删除和修改的文件
6. **数据更新**：根据实际文件更新数据库
7. **文件内容查看**：提供接口查看指定文件的内容（默认显示前4KB）

## 注意事项

- 扫描大型目录可能需要较长时间，具体取决于文件数量和大小
- 程序需要读取文件内容计算哈希值，因此需要足够的文件读取权限
- 对于无法访问的文件，程序会跳过并记录错误信息
- 二进制文件的内容查看功能会以十六进制格式显示前4KB内容

## 示例输出

### 重复文件查找结果

```
找到 3 组重复文件:

组 1: 哈希值 e4d909c290d0fb1ca068ffaddf22cbd0
  - D:\Documents\report.pdf
    大小: 102400 字节
    修改时间: 2023-05-15 14:30:22
  - D:\Backup\documents\report.pdf
    大小: 102400 字节
    修改时间: 2023-06-01 09:15:36

组 2: 哈希值 8c7dd922ad36e50e7c3380ca8d92885b
  - D:\Photos\vacation\IMG_1234.jpg
    大小: 2560000 字节
    修改时间: 2023-07-10 16:45:12
  - D:\Photos\shared\IMG_1234.jpg
    大小: 2560000 字节
    修改时间: 2023-07-11 10:22:45

组 3: 哈希值 5f2b3d0f8c7d1a2e9f4c6b5a8d7e9f1c
  - D:\Projects\app\main.py
    大小: 5120 字节
    修改时间: 2023-08-05 13:10:45
  - D:\Projects\backup\app\main.py
    大小: 5120 字节
    修改时间: 2023-08-05 13:10:45
```

### 目录变更检测结果

```
正在比较目录 'D:\Documents' 与数据库...

目录变更分析结果:
--------------------------------------------------
删除的文件 (2):
  - D:\Documents\old_report.pdf
  - D:\Documents\archive\2022_project.xlsx

新增的文件 (3):
  - D:\Documents\new_project\proposal.pdf
  - D:\Documents\current_plan.xlsx
  - D:\Documents\notes\meeting_minutes.docx

更新的文件 (1):
  - D:\Documents\budget_2023.xlsx

是否要根据目录文件更新数据库？(y/n): 
```

### JSON导出格式示例

```json
{
  "export_time": "2023-09-15 10:30:45",
  "duplicate_groups": [
    {
      "hash": "e4d909c290d0fb1ca068ffaddf22cbd0",
      "files": [
        {
          "path": "D:\\Documents\\report.pdf",
          "size": 102400,
          "created": "2023-05-15 14:30:22",
          "modified": "2023-05-15 14:30:22",
          "owner": "user"
        },
        {
          "path": "D:\\Backup\\documents\\report.pdf",
          "size": 102400,
          "created": "2023-06-01 09:15:36",
          "modified": "2023-06-01 09:15:36",
          "owner": "user"
        }
      ]
    },
    {
      "hash": "8c7dd922ad36e50e7c3380ca8d92885b",
      "files": [
        {
          "path": "D:\\Photos\\vacation\\IMG_1234.jpg",
          "size": 2560000,
          "created": "2023-07-10 16:45:12",
          "modified": "2023-07-10 16:45:12",
          "owner": "user"
        },
        {
          "path": "D:\\Photos\\shared\\IMG_1234.jpg",
          "size": 2560000,
          "created": "2023-07-11 10:22:45",
          "modified": "2023-07-11 10:22:45",
          "owner": "user"
        }
      ]
    }
  ],
  "total_groups": 2
}
```

## 许可证

本项目采用MIT许可证 - 详情请查看LICENSE文件

## 作者

由AI助手(Trae Builder)协助完成