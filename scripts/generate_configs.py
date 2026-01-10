#!/usr/bin/env python3
"""
根据 data 目录下的现有文件结构，自动生成 tables.config 和 files/tables.config 配置文件。
"""

import sys
from pathlib import Path

def generate_tables_config(target_dir: Path):
    """根据 tables/ 目录下的 CSV 文件生成 tables.config"""
    tables_dir = target_dir / "tables"
    
    if not tables_dir.exists():
        return False
    
    # 获取所有 CSV 文件（排除 config.config 等配置文件）
    csv_files = [f.stem for f in tables_dir.glob("*.csv") 
                 if not f.stem.endswith('.config')]
    
    if not csv_files:
        return False
    
    # 排序表名
    csv_files = sorted(csv_files)
    
    # 生成配置文件内容
    config_content = "# Tables configuration\n"
    config_content += "# List of table names to be included in the database\n"
    config_content += "# CSV file names should match table names (e.g., users.csv -> users table)\n"
    config_content += "# Auto-generated based on existing CSV files\n"
    config_content += "\n"
    
    for table_name in csv_files:
        config_content += f"{table_name}\n"
    
    # 写入文件
    config_path = tables_dir / "tables.config"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"  ✓ 生成 tables.config: {len(csv_files)} 个表")
    return True

def generate_files_config(target_dir: Path):
    """根据 files/ 目录下的子目录生成 files/tables.config"""
    files_dir = target_dir / "files"
    
    if not files_dir.exists():
        return False
    
    # 获取所有子目录（排除隐藏目录和文件）
    subdirs = [d.name for d in files_dir.iterdir() 
               if d.is_dir() and not d.name.startswith('.') and d.name != 'tables']
    
    # 过滤掉 tables.config 文件所在的目录（如果存在）
    if 'tables' in subdirs:
        subdirs.remove('tables')
    
    if not subdirs:
        return False
    
    # 排序目录名
    subdirs = sorted(subdirs)
    
    # 生成配置文件内容
    config_content = "# Files tables configuration\n"
    config_content += "# List of table names to be created from subdirectories\n"
    config_content += "# Each subdirectory name should match a table name\n"
    config_content += "# Auto-generated based on existing subdirectories\n"
    config_content += "\n"
    
    for table_name in subdirs:
        config_content += f"{table_name}\n"
    
    # 写入文件
    config_path = files_dir / "tables.config"
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"  ✓ 生成 files/tables.config: {len(subdirs)} 个文件表")
    return True

def process_database(target_name: str, data_dir: Path):
    """处理单个数据库目标目录"""
    target_dir = data_dir / target_name
    
    if not target_dir.exists() or not target_dir.is_dir():
        return False
    
    print(f"\n处理数据库: {target_name}")
    print(f"  目录: {target_dir}")
    
    tables_generated = generate_tables_config(target_dir)
    files_generated = generate_files_config(target_dir)
    
    if not tables_generated and not files_generated:
        print(f"  ⚠ 未找到需要生成配置的内容")
        return False
    
    return True

def main():
    """主函数：为所有数据库目标目录生成配置文件"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        print(f"错误: data 目录不存在: {data_dir}")
        return
    
    # 获取所有数据库目标目录
    targets = []
    for item in data_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 检查是否有 tables 或 files 目录
            if (item / "tables").exists() or (item / "files").exists():
                targets.append(item.name)
    
    if not targets:
        print(f"未找到任何数据库目标目录在 {data_dir}")
        return
    
    print(f"找到 {len(targets)} 个数据库目标目录")
    print(f"开始生成配置文件...\n")
    
    success_count = 0
    for target in sorted(targets):
        if process_database(target, data_dir):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"完成: {success_count}/{len(targets)} 个数据库已处理")
    print(f"{'='*60}")
    
    if success_count == len(targets):
        print("\n✓ 所有配置文件已生成")
    else:
        print(f"\n⚠ 有 {len(targets) - success_count} 个数据库未处理")

if __name__ == "__main__":
    main()
