#!/usr/bin/env python3
"""
Generate db3 database files from schema and data files.
Supports generating multiple db3 files from data subdirectories.
"""

import sqlite3
import csv
import os
import sys
import argparse
from pathlib import Path

def create_database(db_path: str, schema_path: Path):
    """Create database from schema file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read and execute schema if exists
    if schema_path.exists():
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
            cursor.executescript(schema)

    conn.commit()
    return conn

def load_csv_data(conn: sqlite3.Connection, csv_path: Path, table_name: str = None):
    """Load data from CSV file into table."""
    cursor = conn.cursor()
    
    # If table_name not provided, use filename without extension
    if table_name is None:
        table_name = csv_path.stem
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        
        if columns:
            # Create table if not exists
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            placeholders = []
            for col in columns:
                create_table_sql += f"{col} TEXT, "
            create_table_sql = create_table_sql.rstrip(", ") + ")"
            cursor.execute(create_table_sql)
            
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)
            
            for row in reader:
                values = [row[col] for col in columns]
                cursor.execute(
                    f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    values
                )
    
    conn.commit()

def load_config(conn: sqlite3.Connection, config_path: Path):
    """Load configuration from .config file into config table.
    
    Config file format (simple key=value or key:value):
    database.name=ZWCAD_Arch.db3
    database.version=1.0.0
    arch.enabled=true
    arch.default_style=modern
    
    Or with colon separator:
    database.name: ZWCAD_Arch.db3
    database.version: 1.0.0
    """
    cursor = conn.cursor()
    
    # Ensure config table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    if not config_path.exists():
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            # Strip whitespace and skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Support both = and : separators
            if '=' in line:
                key, value = line.split('=', 1)
            elif ':' in line:
                key, value = line.split(':', 1)
            else:
                # Skip invalid lines
                continue
            
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            if key and value:
                cursor.execute(
                    "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                    (key, value)
                )
    
    conn.commit()

def load_sql_script(conn: sqlite3.Connection, sql_path: Path):
    """Execute SQL script file."""
    cursor = conn.cursor()
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
        cursor.executescript(sql)
    
    conn.commit()

def load_tables_config(config_path: Path):
    """Load table names from tables.config configuration file.
    
    Config file format (one table name per line):
    users
    config
    logs
    
    Or with tables= prefix:
    tables=users,config,logs
    """
    if not config_path.exists():
        return []
    
    try:
        tables = []
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Support tables= format
                if line.startswith('tables='):
                    table_list = line.split('=', 1)[1].strip()
                    tables.extend([t.strip() for t in table_list.split(',') if t.strip()])
                else:
                    # Simple format: one table name per line
                    tables.append(line)
        
        return [t for t in tables if t]  # Remove empty strings
    except Exception as e:
        print(f"Warning: Error loading tables config from {config_path}: {e}")
    
    return []

def load_files_from_directory(conn: sqlite3.Connection, table_name: str, files_dir: Path):
    """Load files from a directory into a table with ID, code, file_blob columns."""
    cursor = conn.cursor()
    
    # Create table with ID, code, file_blob structure
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            file_blob BLOB NOT NULL
        )
    """)
    
    if not files_dir.exists() or not files_dir.is_dir():
        return 0
    
    file_count = 0
    # Get all files in the directory (non-recursive)
    for file_path in files_dir.iterdir():
        if file_path.is_file():
            try:
                # Read file as binary
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Get filename (code)
                code = file_path.name
                
                # Insert into table
                cursor.execute(
                    f"INSERT INTO {table_name} (code, file_blob) VALUES (?, ?)",
                    (code, sqlite3.Binary(file_data))
                )
                file_count += 1
            except Exception as e:
                print(f"    ✗ Error loading file {file_path.name}: {e}")
    
    conn.commit()
    return file_count

def build_database(target_name: str, project_root: Path, build_dir: Path):
    """Build a single database from target directory."""
    target_dir = project_root / "data" / target_name
    
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Warning: Target directory not found: {target_dir}")
        return False
    
    db_path = build_dir / f"{target_name}.db3"
    schema_path = target_dir / "schema.sql"
    tables_dir = target_dir / "tables"
    files_dir = target_dir / "files"
    
    # Remove existing database if present
    if db_path.exists():
        os.remove(db_path)
    
    print(f"\n{'='*60}")
    print(f"Building database: {target_name}")
    print(f"Output: {db_path}")
    print(f"{'='*60}")
    
    # Create database from schema
    conn = create_database(str(db_path), schema_path)
    if schema_path.exists():
        print("✓ Schema loaded successfully")
    
    # Load CSV files from tables directory (only those specified in tables.config)
    if tables_dir.exists():
        tables_config_path = tables_dir / "tables.config"
        specified_tables = load_tables_config(tables_config_path)
        
        if specified_tables:
            print(f"  Processing {len(specified_tables)} specified table(s) from tables.config...")
            for table_name in specified_tables:
                csv_file = tables_dir / f"{table_name}.csv"
                if csv_file.exists():
                    try:
                        load_csv_data(conn, csv_file, table_name)
                        print(f"  ✓ Loaded table '{table_name}' from {csv_file.name}")
                    except Exception as e:
                        print(f"  ✗ Error loading table '{table_name}' from {csv_file.name}: {e}")
                else:
                    print(f"  ⚠ CSV file not found for table '{table_name}': {csv_file.name}")
        else:
            # If no tables.config or empty, process all CSV files (backward compatibility)
            csv_files = list(tables_dir.glob("*.csv"))
            for csv_file in csv_files:
                # Skip config files
                if csv_file.name.endswith('.config'):
                    continue
                try:
                    load_csv_data(conn, csv_file)
                    print(f"  ✓ Loaded {csv_file.name} (no tables.config found, using all CSV files)")
                except Exception as e:
                    print(f"  ✗ Error loading {csv_file.name}: {e}")
    
    # Load config files (excluding tables.config)
    if tables_dir.exists():
        config_files = list(tables_dir.glob("*.config"))
        for config_file in config_files:
            # Skip tables.config configuration file
            if config_file.name == "tables.config":
                continue
            try:
                load_config(conn, config_file)
                print(f"  ✓ Loaded config from {config_file.name}")
            except Exception as e:
                print(f"  ✗ Error loading {config_file.name}: {e}")
    
    # Execute SQL scripts (excluding schema.sql)
    if tables_dir.exists():
        sql_files = [f for f in tables_dir.glob("*.sql") if f.name != "schema.sql"]
        for sql_file in sql_files:
            try:
                load_sql_script(conn, sql_file)
                print(f"  ✓ Executed {sql_file.name}")
            except Exception as e:
                print(f"  ✗ Error executing {sql_file.name}: {e}")
    
    # Load files from subdirectories into tables with ID, code, file_blob structure
    if files_dir.exists():
        files_config_path = files_dir / "tables.config"
        specified_file_tables = load_tables_config(files_config_path)
        
        if specified_file_tables:
            print(f"  Processing {len(specified_file_tables)} file table(s) from files/tables.config...")
            for table_name in specified_file_tables:
                table_files_dir = files_dir / table_name
                if table_files_dir.exists() and table_files_dir.is_dir():
                    try:
                        file_count = load_files_from_directory(conn, table_name, table_files_dir)
                        if file_count > 0:
                            print(f"  ✓ Created table '{table_name}' with {file_count} file(s)")
                        else:
                            print(f"  ⚠ Table '{table_name}' created but no files found in {table_name}/")
                    except Exception as e:
                        print(f"  ✗ Error processing file table '{table_name}': {e}")
                else:
                    print(f"  ⚠ Directory not found for file table '{table_name}': {table_files_dir}")
        else:
            print("  ℹ No files/tables.config found or empty, skipping file tables")
    
    conn.close()
    print(f"✓ Database built successfully: {db_path}")
    return True

def get_available_targets(project_root: Path):
    """Get list of available database targets from data directory."""
    data_dir = project_root / "data"
    if not data_dir.exists():
        return []
    
    targets = []
    for item in data_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a valid target directory (has tables or files subdirectory)
            if (item / "tables").exists() or (item / "files").exists() or (item / "schema.sql").exists():
                targets.append(item.name)
    
    return sorted(targets)

def main():
    """Main function to build databases."""
    parser = argparse.ArgumentParser(
        description='Generate db3 database files from data directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build all available databases
  python scripts/build_db.py --all
  
  # Build specific databases
  python scripts/build_db.py ZWCAD_Arch USERCompLib
  
  # List available targets
  python scripts/build_db.py --list
        """
    )
    
    parser.add_argument(
        'targets',
        nargs='*',
        help='Specific database targets to build (e.g., ZWCAD_Arch USERCompLib)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Build all available databases'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available database targets'
    )
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Get available targets
    available_targets = get_available_targets(project_root)
    
    # List targets if requested
    if args.list:
        print("Available database targets:")
        for target in available_targets:
            print(f"  - {target}")
        return
    
    # Determine which targets to build
    if args.all:
        targets_to_build = available_targets
        if not targets_to_build:
            print("No available targets found in data directory.")
            return
    elif args.targets:
        targets_to_build = args.targets
        # Validate targets
        invalid_targets = [t for t in targets_to_build if t not in available_targets]
        if invalid_targets:
            print(f"Error: Invalid targets: {', '.join(invalid_targets)}")
            print(f"Available targets: {', '.join(available_targets)}")
            sys.exit(1)
    else:
        parser.print_help()
        print(f"\nAvailable targets: {', '.join(available_targets)}")
        print("\nUse --all to build all targets or specify target names.")
        sys.exit(1)
    
    # Build databases
    print(f"Building {len(targets_to_build)} database(s)...")
    success_count = 0
    
    for target in targets_to_build:
        if build_database(target, project_root, build_dir):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(targets_to_build)} database(s) built successfully")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
