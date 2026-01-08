#!/usr/bin/env python3
"""
Export data from db3 database files.
Optional utility to extract data from the built databases.
"""

import sqlite3
import csv
import json
import sys
import argparse
from pathlib import Path

def export_table_to_csv(conn: sqlite3.Connection, table_name: str, output_path: Path):
    """Export a table to CSV file."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    
    print(f"  Exported {len(rows)} rows from '{table_name}' to {output_path.name}")

def export_table_to_json(conn: sqlite3.Connection, table_name: str, output_path: Path):
    """Export a table to JSON file."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    data = [dict(zip(columns, row)) for row in rows]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"  Exported {len(rows)} rows from '{table_name}' to {output_path.name}")

def is_file_table(table_name: str, conn: sqlite3.Connection):
    """Check if a table is a file table (has ID, code, file_blob columns)."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Get column names
    col_names = [col[1].lower() for col in columns]
    
    # Check if it has ID, code, file_blob structure
    has_id = 'id' in col_names
    has_code = 'code' in col_names
    has_blob = 'file_blob' in col_names or 'fileblob' in col_names
    
    return has_id and has_code and has_blob

def export_file_table(conn: sqlite3.Connection, table_name: str, output_dir: Path):
    """Export a file table (ID, code, file_blob) to directory structure."""
    cursor = conn.cursor()
    
    # Get column names first to handle case sensitivity
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    col_names = {}
    for col in columns_info:
        col_names[col[1].lower()] = col[1]  # Store original case
    
    # Build SELECT query with proper column names
    id_col = col_names.get('id', 'ID')
    code_col = col_names.get('code', 'code')
    blob_col = col_names.get('file_blob', col_names.get('fileblob', 'file_blob'))
    
    cursor.execute(f"SELECT {id_col}, {code_col}, {blob_col} FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"  ⚠ Table '{table_name}' is empty")
        return 0
    
    # Create subdirectory for this table
    table_dir = output_dir / table_name
    table_dir.mkdir(parents=True, exist_ok=True)
    
    file_count = 0
    for row in rows:
        file_id, code, file_blob = row
        if file_blob and code:
            file_path = table_dir / code
            try:
                with open(file_path, 'wb') as f:
                    if isinstance(file_blob, bytes):
                        f.write(file_blob)
                    else:
                        f.write(bytes(file_blob))
                file_count += 1
            except Exception as e:
                print(f"    ✗ Error writing file {code}: {e}")
    
    print(f"  Exported {file_count} file(s) from table '{table_name}' to {table_dir.name}/")
    return file_count

def list_tables(conn: sqlite3.Connection):
    """List all tables in the database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def show_table_info(conn: sqlite3.Connection, table_name: str):
    """Show information about a table."""
    cursor = conn.cursor()
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n  Table: {table_name}")
    print(f"  Rows: {row_count}")
    print("  Columns:")
    for col in columns:
        col_id, name, col_type, not_null, default_val, pk = col
        pk_str = " (PRIMARY KEY)" if pk else ""
        null_str = " NOT NULL" if not_null else ""
        default_str = f" DEFAULT {default_val}" if default_val else ""
        print(f"    - {name}: {col_type}{null_str}{default_str}{pk_str}")

def get_available_databases(build_dir: Path):
    """Get list of available db3 files in build directory."""
    if not build_dir.exists():
        return []
    
    db_files = list(build_dir.glob("*.db3"))
    return sorted([db.stem for db in db_files])

def export_database_from_path(db_path: Path, output_dir: Path = None, show_info: bool = False, 
                               export_csv: bool = True, export_json: bool = False):
    """Export a database from specified path to output directory.
    
    Args:
        db_path: Path to the database file
        output_dir: Output directory (default: same as db file directory)
        show_info: Whether to show detailed table information
        export_csv: Whether to export CSV files (default: True)
        export_json: Whether to export JSON files (default: False)
    """
    if not db_path.exists():
        print(f"Error: Database file not found: {db_path}")
        return False
    
    # If output_dir not specified, use the same directory as db file
    if output_dir is None:
        output_dir = db_path.parent
    
    db_name = db_path.stem
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    print(f"\n{'='*60}")
    print(f"Exporting database: {db_name}")
    print(f"Source: {db_path}")
    print(f"Output: {output_dir}")
    print(f"Format: CSV={export_csv}, JSON={export_json}")
    print(f"{'='*60}")
    
    # List all tables
    tables = list_tables(conn)
    
    if not tables:
        print("  No tables found in database.")
        conn.close()
        return False
    
    # Show table info if requested
    if show_info:
        print(f"\nFound {len(tables)} table(s):")
        for table in tables:
            show_table_info(conn, table)
    
    # Create export directories
    tables_dir = output_dir / "tables"
    files_dir = output_dir / "files"
    tables_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)
    
    # Separate tables into data tables and file tables
    data_tables = []
    file_tables = []
    
    for table in tables:
        if is_file_table(table, conn):
            file_tables.append(table)
        else:
            data_tables.append(table)
    
    # Export data tables to tables directory
    if data_tables:
        print(f"\nExporting data tables to: {tables_dir}")
        for table in data_tables:
            try:
                if export_csv:
                    csv_path = tables_dir / f"{table}.csv"
                    export_table_to_csv(conn, table, csv_path)
                if export_json:
                    json_path = tables_dir / f"{table}.json"
                    export_table_to_json(conn, table, json_path)
            except Exception as e:
                print(f"  ✗ Error exporting table '{table}': {e}")
    
    # Export file tables to files directory
    if file_tables:
        print(f"\nExporting file tables to: {files_dir}")
        for table in file_tables:
            try:
                export_file_table(conn, table, files_dir)
            except Exception as e:
                print(f"  ✗ Error exporting file table '{table}': {e}")
    
    conn.close()
    print(f"\n✓ Export completed for {db_name}")
    return True

def export_database(db_name: str, project_root: Path, build_dir: Path, export_dir: Path, 
                    show_info: bool = False, export_csv: bool = True, export_json: bool = False):
    """Export a single database (legacy function for backward compatibility)."""
    db_path = build_dir / f"{db_name}.db3"
    
    # Use the database name as export directory name
    db_export_dir = export_dir / db_name
    return export_database_from_path(db_path, db_export_dir, show_info, export_csv, export_json)

def main():
    """Main function to export databases."""
    parser = argparse.ArgumentParser(
        description='Export data from db3 database files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export all available databases from build directory
  python scripts/export_db.py --all
  
  # Export specific databases from build directory
  python scripts/export_db.py ZWCAD_Arch USERCompLib
  
  # Export a specific db3 file to its same directory
  python scripts/export_db.py --file build/ZWCAD_Arch.db3
  
  # Export a db3 file to a specific directory
  python scripts/export_db.py --file path/to/database.db3 --output output_dir
  
  # Export only CSV (default)
  python scripts/export_db.py --file build/ZWCAD_Arch.db3
  
  # Export only JSON
  python scripts/export_db.py --file build/ZWCAD_Arch.db3 --no-csv --json
  
  # Export both CSV and JSON
  python scripts/export_db.py --file build/ZWCAD_Arch.db3 --json
  
  # List available databases
  python scripts/export_db.py --list
  
  # Show detailed table information
  python scripts/export_db.py --file build/ZWCAD_Arch.db3 --info
        """
    )
    
    parser.add_argument(
        'databases',
        nargs='*',
        help='Specific databases to export (e.g., ZWCAD_Arch USERCompLib)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Export all available databases from build directory'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available database files in build directory'
    )
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Show detailed table information'
    )
    parser.add_argument(
        '--file', '-f',
        type=str,
        help='Path to a specific db3 file to export'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory (default: same directory as db3 file)'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        default=None,
        help='Explicitly enable CSV export (default: enabled)'
    )
    parser.add_argument(
        '--no-csv',
        dest='csv',
        action='store_false',
        help='Disable CSV export (use with --json to export only JSON)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        default=False,
        help='Also export JSON format (default: only CSV is exported)'
    )
    
    args = parser.parse_args()
    
    # Set default: CSV enabled by default, JSON disabled by default
    export_csv = args.csv if args.csv is not None else True
    export_json = args.json
    
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    export_dir = project_root / "build" / "export"
    
    # Handle --file option (export specific db3 file)
    if args.file:
        db_path = Path(args.file)
        if not db_path.is_absolute():
            # Try relative to current directory first
            if not db_path.exists():
                # Try relative to project root
                db_path = project_root / args.file
        
        output_dir = None
        if args.output:
            output_dir = Path(args.output)
            if not output_dir.is_absolute():
                output_dir = project_root / args.output
        
        export_database_from_path(db_path, output_dir, args.info, export_csv, export_json)
        return
    
    # Get available databases
    available_databases = get_available_databases(build_dir)
    
    # List databases if requested
    if args.list:
        print("Available database files in build directory:")
        if available_databases:
            for db in available_databases:
                db_path = build_dir / f"{db}.db3"
                size = db_path.stat().st_size
                size_kb = size / 1024
                print(f"  - {db} ({size_kb:.2f} KB)")
        else:
            print("  No database files found. Run build_db.py first.")
        return
    
    # Determine which databases to export
    if args.all:
        databases_to_export = available_databases
        if not databases_to_export:
            print("No database files found in build directory.")
            print("Please run build_db.py first to create databases.")
            return
    elif args.databases:
        databases_to_export = args.databases
        # Validate databases
        invalid_dbs = [db for db in databases_to_export if db not in available_databases]
        if invalid_dbs:
            print(f"Error: Database files not found: {', '.join(invalid_dbs)}")
            print(f"Available databases: {', '.join(available_databases)}")
            sys.exit(1)
    else:
        parser.print_help()
        if available_databases:
            print(f"\nAvailable databases: {', '.join(available_databases)}")
            print("\nUse --all to export all databases or specify database names.")
            print("Or use --file to export a specific db3 file.")
        else:
            print("\nNo database files found. Run build_db.py first.")
            print("Or use --file to export a specific db3 file.")
        sys.exit(1)
    
    # Export databases
    print(f"Exporting {len(databases_to_export)} database(s)...")
    success_count = 0
    
    for db_name in databases_to_export:
        if export_database(db_name, project_root, build_dir, export_dir, args.info, export_csv, export_json):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(databases_to_export)} database(s) exported successfully")
    print(f"Export directory: {export_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
