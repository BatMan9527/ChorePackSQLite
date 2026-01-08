#!/usr/bin/env python3
"""
将 build 目录下的所有 db3 文件导出并同步到 data 目录下对应的数据库目标目录。
"""

import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.export_db import export_database_from_path

def sync_database_to_data(db_file: Path, project_root: Path):
    """将单个 db3 文件同步到 data 目录下对应的目标目录。"""
    db_name = db_file.stem
    
    # 确定目标目录：data/{数据库名}/
    target_dir = project_root / "data" / db_name
    
    if not target_dir.exists():
        print(f"  ⚠ 目标目录不存在，正在创建: {target_dir}")
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 tables 和 files 子目录
    tables_dir = target_dir / "tables"
    files_dir = target_dir / "files"
    tables_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"同步数据库: {db_name}")
    print(f"源文件: {db_file}")
    print(f"目标目录: {target_dir}")
    print(f"{'='*60}")
    
    # 导出到目标目录（tables/ 和 files/ 会自动创建）
    try:
        success = export_database_from_path(db_file, target_dir, show_info=False, 
                                           export_csv=True, export_json=False)
        if success:
            print(f"✓ {db_name} 同步成功")
            return True
        else:
            print(f"✗ {db_name} 同步失败")
            return False
    except Exception as e:
        print(f"✗ 同步 {db_name} 时出错: {e}")
        return False

def main():
    """主函数：同步所有 build 目录下的 db3 文件到 data 目录。"""
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    
    if not build_dir.exists():
        print(f"错误: build 目录不存在: {build_dir}")
        return
    
    # 获取所有 db3 文件
    db_files = list(build_dir.glob("*.db3"))
    
    if not db_files:
        print(f"未找到任何 db3 文件在 {build_dir}")
        return
    
    print(f"找到 {len(db_files)} 个 db3 文件")
    print(f"开始同步到 data 目录...\n")
    
    success_count = 0
    for db_file in sorted(db_files):
        if sync_database_to_data(db_file, project_root):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"同步完成: {success_count}/{len(db_files)} 个数据库同步成功")
    print(f"{'='*60}")
    
    if success_count == len(db_files):
        print("\n✓ 所有数据库已成功同步到 data 目录")
    else:
        print(f"\n⚠ 有 {len(db_files) - success_count} 个数据库同步失败")

if __name__ == "__main__":
    main()
