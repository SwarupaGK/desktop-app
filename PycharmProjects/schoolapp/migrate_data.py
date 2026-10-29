#!/usr/bin/env python3
"""
Data Migration Tool - Export development database to .exe bundle

This script copies all records from development database to the bundled database
that will be included in the .exe file, ensuring users can see all data
entered during normal execution.
"""

import os
import sys
import shutil
import sqlite3
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_PATH, resource_path, data_path

def migrate_dev_to_bundle():
    """Copy all records from development database to bundled database for .exe distribution."""
    
    print("🔄 Starting Data Migration...")
    print(f"Source: {DB_PATH}")
    
    # Development database path
    dev_db_path = DB_PATH
    
    # Target bundled database path (for .exe)
    bundle_db_path = resource_path("data/students.db")
    
    if not os.path.exists(dev_db_path):
        print(f"❌ Development database not found: {dev_db_path}")
        return False
    
    if not os.path.exists(os.path.dirname(bundle_db_path)):
        os.makedirs(os.path.dirname(bundle_db_path), exist_ok=True)
        print(f"📁 Created bundle directory: {os.path.dirname(bundle_db_path)}")
    
    # Backup existing bundle database if it exists
    if os.path.exists(bundle_db_path):
        backup_path = bundle_db_path.replace('.db', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(bundle_db_path, backup_path)
        print(f"💾 Backed up existing bundle to: {backup_path}")
    
    try:
        # Copy development database to bundle location
        shutil.copy2(dev_db_path, bundle_db_path)
        print(f"✅ Successfully migrated data to: {bundle_db_path}")
        
        # Verify the migration
        dev_conn = sqlite3.connect(dev_db_path)
        bundle_conn = sqlite3.connect(bundle_db_path)
        
        dev_cur = dev_conn.cursor()
        bundle_cur = bundle_conn.cursor()
        
        dev_cur.execute("SELECT COUNT(*) FROM students")
        bundle_cur.execute("SELECT COUNT(*) FROM students")
        
        dev_count = dev_cur.fetchone()[0]
        bundle_count = bundle_cur.fetchone()[0]
        
        dev_conn.close()
        bundle_conn.close()
        
        print(f"📊 Migration Summary:")
        print(f"   Development records: {dev_count}")
        print(f"   Bundle records: {bundle_count}")
        print(f"   Status: {'✅ Success' if dev_count == bundle_count else '⚠️  Mismatch'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False

def main():
    """Main function for data migration."""
    if len(sys.argv) > 1 and sys.argv[1] == "--migrate":
        migrate_dev_to_bundle()
    else:
        print("Data Migration Tool")
        print("Usage: python migrate_data.py --migrate")
        print("")
        print("This tool copies all development database records to the bundled database")
        print("that will be included in the .exe file.")
        print("")
        print("Run this before building the .exe file to include all user data.")

if __name__ == "__main__":
    main()
