# ChorePackSQLite

自动生成多个独立的 SQLite 数据库文件（db3）的项目。

## 项目结构

```
project/
├── data/
│   ├── World/          # 数据库目标目录
│   │   ├── schema.sql       # 表结构定义（可选）
│   │   ├── tables/          # 数据文件目录
│   │   │   ├── tables.config    # 表配置：指定需要处理的CSV表名列表
│   │   │   ├── *.csv        # CSV数据文件（文件名即为表名）
│   │   │   ├── *.config     # 其他配置文件（key=value格式，导入到config表）
│   │   │   └── *.sql        # SQL脚本文件
│   │   └── files/           # 二进制文件目录
│   │       ├── tables.config # 文件表配置：指定需要创建的表名列表
│   │       └── {表名}/      # 子目录名即为表名
│   │           └── *.bin    # 子目录中的文件
│   └── Others/
│
├── scripts/
│   ├── build_db.py          # 生成 db3 文件
│   ├── export_db.py         # 从 db3 导出数据
│   ├── export_all.ps1       # 导出脚本
│   ├── export_all.py        # 导出脚本
│   ├── export_all.sh        # 导出脚本
│   ├── generate_configs.py  # 生成 data 目录现有结构配置文件
│   └── sync_from_build.py   # 从 build 目录同步到 data 目录
│
├── build/                   # 输出目录
│   ├── *.db3                # 生成的数据库文件
│   └── export/              # 导出的数据文件
│
└── requirements.txt         # Python 依赖
```

## 配置说明

### tables/tables.config

指定需要处理并加入到数据库的CSV表名列表。CSV文件名应与表名匹配。

```
# Tables configuration
# 简单格式：每行一个表名
users
config
logs
```

### files/tables.config

指定需要创建的文件表名列表。每个表名对应 `files/` 目录下的一个子目录。

```
# Files tables configuration
# 简单格式：每行一个表名
images
documents
resources
```

### 配置文件格式说明

配置文件使用简单的文本格式，支持以下特性：
- 使用 `#` 开头的行作为注释
- 支持 `key=value` 或 `key: value` 格式
- 值可以包含引号（会自动去除）
- 支持嵌套键名（使用点号分隔，如 `database.name`）

每个文件表会自动创建以下结构：
- `ID`: 自动递增的主键
- `code`: 文件名
- `file_blob`: 文件的二进制内容（BLOB）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 生成数据库文件

#### 生成所有数据库
```bash
python scripts/build_db.py --all
```

#### 生成指定的数据库
```bash
python scripts/build_db.py World
```

#### 为data目录现有数据生成配置文件
```bash
python scripts/generate_configs.py
```

#### 列出所有可用的目标
```bash
python scripts/build_db.py --list
```

### 导出数据库数据

#### 导出所有数据库
```bash
python scripts/export_db.py --all
```

#### 导出指定的数据库
```bash
python scripts/export_db.py World
```

#### 显示详细表信息
```bash
python scripts/export_db.py World --info
```

#### 列出所有可用的数据库文件
```bash
python scripts/export_db.py --list
```

## 数据库目标目录结构说明

每个数据库目标目录（如 `World`）应包含：

### 1. schema.sql（可选）
表结构定义。如果不存在，脚本会为CSV和文件表自动创建表结构。

### 2. tables/ 目录

包含以下文件：

- **tables.config**（必需）：配置文件，指定需要处理的表名列表
  ```
  # 简单格式：每行一个表名
  users
  config
  logs
  
  # 或使用逗号分隔格式
  tables=users,config,logs
  ```

- **\*.csv**：CSV数据文件
  - 文件名即为表名（例如：`users.csv` → `users` 表）
  - 只有 `tables.config` 中指定的表才会被处理

- **\*.config**（可选）：其他配置文件
  - 使用简单的 key=value 格式
  - 会被导入到 `config` 表
  - `tables.config` 不会被导入
  - 示例：
    ```
    database.name=World.db3
    database.version=1.0.0
    arch.enabled=true
    ```

- **\*.sql**（可选）：SQL脚本文件
  - 会被执行
  - `schema.sql` 不会被处理

### 3. files/ 目录

包含以下内容：

- **tables.config**（必需）：配置文件，指定需要创建的文件表名列表
  ```
  # 简单格式：每行一个表名
  images
  documents
  resources
  ```

- **{表名}/**：子目录
  - 子目录名对应 `tables.config` 中配置的表名
  - 每个子目录中的文件会被存储到对应的表中
  - 表结构：`ID`（自动递增），`code`（文件名），`file_blob`（文件内容）


## 输出

生成的数据库文件将保存在 `build/` 目录下，文件名格式为 `{目标名称}.db3`。

例如：
- `build/World.db3`

## 工作流程示例

1. **准备数据**：
   - 在 `data/World/tables/` 中创建 `tables.config` 配置文件
   - 创建对应的 CSV 文件（如 `users.csv`）
   - 在 `data/World/files/` 中创建 `tables.config` 配置文件
   - 创建对应的子目录（如 `images/`）并在其中放置文件

2. **生成数据库**：
   ```bash
   python scripts/build_db.py World
   ```

3. **验证结果**：
   ```bash
   python scripts/export_db.py World --info
   ```

## 注意事项

- `build/` 目录和 `*.db3` 文件已添加到 `.gitignore`，不会被版本控制
- 每个目标目录都会生成独立的数据库文件
- CSV 文件的表名必须与文件名匹配（不含扩展名）
- 只有 `tables.config` 中指定的表才会被处理
- 文件表会自动创建 `ID`、`code`、`file_blob` 三列结构
- 如果 `tables.config` 不存在或为空，会回退到处理所有 CSV 文件（向后兼容）
- 配置文件使用简单的 key=value 格式，无需 YAML 解析库



# 导出 db3 文件使用指南


## 导出方法

### 方法 1: 导出所有数据库（推荐）

导出 build 目录下的所有 db3 文件，每个文件会导出到 `build/export/{数据库名}/` 目录：

```bash
python scripts/export_db.py --all
```

### 方法 2: 导出指定的数据库

只导出指定的数据库：

```bash
# 导出单个数据库
python scripts/export_db.py World

# 导出多个数据库
python scripts/export_db.py World Others
```

### 方法 3: 导出指定 db3 文件到同目录下

将指定的 db3 文件导出到其所在目录的 `tables/` 和 `files/` 目录：

```bash
# 导出单个文件到同目录下
python scripts/export_db.py --file build/World.db3

# 导出多个文件到各自的目录下
python scripts/export_db.py --file build/World.db3
python scripts/export_db.py --file build/Other.db3
```

### 方法 4: 导出到指定目录

将 db3 文件导出到指定的目录：

```bash
python scripts/export_db.py --file build/World.db3 --output output_dir
```

## 导出结构说明

### 使用 --all 或指定数据库名称（方法 1、2）

导出结构：
```
build/
└── export/
    ├── World/
    │   ├── tables/
    │   │   ├── *.csv
    │   │   └── *.json
    │   └── files/
    │       └── {表名}/
    │           └── *.bin
    ├── Others/
    │   └── ...
    └── ...
```

### 使用 --file 参数（方法 3）

导出结构（在 db3 文件所在目录）：
```
build/
├── World.db3
├── tables/
│   ├── *.csv
│   └── *.json
└── files/
    └── {表名}/
        └── *.bin
```

## 查看表信息

在导出前，可以先查看数据库中的表信息：

```bash
# 查看指定文件的所有表信息
python scripts/export_db.py --file build/World.db3 --info

# 查看所有可用数据库
python scripts/export_db.py --list
```

## 批量导出（推荐）

已提供批量导出脚本，可以直接使用：

### Python 脚本（跨平台）
```bash
python scripts/export_all.py
```

### PowerShell 脚本（Windows）
```powershell
.\scripts\export_all.ps1
```

### Bash 脚本（Linux/Mac）
```bash
bash scripts/export_all.sh
```

这些脚本会自动：
1. 扫描 build 目录下的所有 .db3 文件
2. 将每个文件导出到其所在目录的 `tables/` 和 `files/` 目录
3. 显示导出进度和结果

## 手动批量导出

如果需要手动批量导出，可以使用以下命令：

### PowerShell
```powershell
# 批量导出 build 目录下所有 db3 文件
Get-ChildItem -Path build -Filter *.db3 | ForEach-Object {
    python scripts/export_db.py --file $_.FullName
}
```

### Python
```python
from pathlib import Path
import subprocess

build_dir = Path("build")
for db_file in build_dir.glob("*.db3"):
    subprocess.run(["python", "scripts/export_db.py", "--file", str(db_file)])
```

## 导出格式选项

默认只导出 CSV 格式，可以可选地导出 JSON：

```bash
# 默认：只导出 CSV（推荐）
python scripts/export_db.py --file build/World.db3

# 同时导出 CSV 和 JSON
python scripts/export_db.py --file build/World.db3 --json

# 只导出 JSON（不导出 CSV）
python scripts/export_db.py --file build/World.db3 --no-csv --json

# 明确指定导出 CSV（默认行为，可选）
python scripts/export_db.py --file build/World.db3 --csv
```

## 注意事项

1. **默认行为**：只导出 CSV 格式，不导出 JSON（节省空间和时间）
2. 导出过程会自动识别文件表（包含 `ID`、`code`、`file_blob` 列）和普通数据表
3. 普通数据表会根据格式选项导出到 `tables/` 目录
4. 文件表始终会将二进制文件导出到 `files/{表名}/` 目录
5. 如果输出目录已存在，会覆盖同名文件
6. 使用 `--file` 参数时，如果没有指定 `--output`，会导出到 db3 文件所在目录



# 从 build 目录同步到 data 目录

将 build 目录下的所有 db3 文件导出并同步到 data 目录下对应的数据库目标目录。

## 功能说明

这个脚本会：
1. 扫描 `build/` 目录下的所有 `.db3` 文件
2. 将每个数据库导出到对应的 `data/{数据库名}/` 目录
3. 在目标目录下创建 `tables/` 和 `files/` 目录
4. 将数据表导出为 CSV 到 `tables/` 目录
5. 将文件表导出二进制文件到 `files/{表名}/` 目录

## 使用方法

### 基本用法

```bash
python scripts/sync_from_build.py
```

### 同步结果

对于 `build/World.db3`，会同步到：
```
data/
└── World/
    ├── tables/
    │   ├── users.csv
    │   ├── config.csv
    │   └── ...
    └── files/
        ├── images/
        │   ├── logo.png
        │   └── icon.png
        ├── documents/
        │   └── readme.txt
        └── ...
```

## 注意事项

1. **覆盖现有文件**：同步会覆盖目标目录中已存在的同名文件
2. **自动创建目录**：如果目标目录不存在，会自动创建
3. **只导出 CSV**：默认只导出 CSV 格式，不导出 JSON（节省空间）
4. **保留 schema.sql**：不会覆盖或删除现有的 `schema.sql` 文件
5. **保留配置文件**：不会覆盖或删除现有的 `tables.config` 和 `config.config` 文件

## 使用场景

- 从外部获取的 db3 文件需要同步到项目结构
- 更新 build 目录中的 db3 文件后，需要同步到 data 目录
- 从备份恢复数据库到项目结构

## 示例输出

```
找到 1 个 db3 文件
开始同步到 data 目录...

============================================================
同步数据库: World
源文件: build\World.db3
目标目录: data\World
============================================================
...
✓ World 同步成功

============================================================
同步完成: 1/1 个数据库同步成功
============================================================

✓ 所有数据库已成功同步到 data 目录
```
