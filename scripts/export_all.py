#!/usr/bin/env python3
"""
批量导出 build 目录下所有 db3 文件到各自的目录
直接调用 export_db.py 的命令行功能
"""

import subprocess
import sys
from pathlib import Path

def main():
    """批量导出所有 db3 文件"""
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    
    if not build_dir.exists():
        print(f"错误: build 目录不存在: {build_dir}")
        return
    
    db_files = list(build_dir.glob("*.db3"))
    
    if not db_files:
        print(f"未找到任何 db3 文件在 {build_dir}")
        return
    
    print(f"正在导出 build 目录下的所有 db3 文件...")
    print(f"找到 {len(db_files)} 个文件\n")
    
    success_count = 0
    for db_file in sorted(db_files):
        db_name = db_file.stem
        print(f"{'='*60}")
        print(f"正在处理: {db_name}")
        print(f"{'='*60}")
        
        try:
            # 调用 export_db.py 的 --file 参数
            result = subprocess.run(
                [sys.executable, "scripts/export_db.py", "--file", str(db_file)],
                cwd=project_root,
                capture_output=False
            )
            
            if result.returncode == 0:
                success_count += 1
                print(f"\n✓ {db_name} 导出成功\n")
            else:
                print(f"\n✗ {db_name} 导出失败\n")
        except Exception as e:
            print(f"✗ 导出 {db_name} 时出错: {e}\n")
    
    print(f"{'='*60}")
    print(f"完成: {success_count}/{len(db_files)} 个文件导出成功")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
