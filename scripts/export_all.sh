#!/bin/bash
# 批量导出 build 目录下所有 db3 文件到各自的目录

cd "$(dirname "$0")/.."

echo "正在导出 build 目录下的所有 db3 文件..."
echo ""

for db_file in build/*.db3; do
    if [ -f "$db_file" ]; then
        db_name=$(basename "$db_file" .db3)
        echo "正在导出: $db_name"
        python scripts/export_db.py --file "$db_file"
        echo ""
    fi
done

echo "所有文件导出完成！"
