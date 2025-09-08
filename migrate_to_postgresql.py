#!/usr/bin/env python3
"""
Data migration script from SQLite to PostgreSQL for WebSpider
"""

import sys
import os
import sqlite3
import psycopg2
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webspider.config import DatabaseConfig
from scripts.setup_postgresql import PostgreSQLSetup


def backup_sqlite_database(sqlite_path, backup_path=None):
    """Create a backup of the SQLite database before migration"""
    if not os.path.exists(sqlite_path):
        print(f"SQLite database '{sqlite_path}' not found.")
        return False
    
    if backup_path is None:
        backup_path = f"{sqlite_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        import shutil
        shutil.copy2(sqlite_path, backup_path)
        print(f"SQLite database backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to backup SQLite database: {e}")
        return False


def migrate_data():
    """Main migration function"""
    print("=== WebSpider Database Migration: SQLite to PostgreSQL ===\n")
    
    # Step 1: Check if SQLite database exists
    sqlite_path = "spider_urls.db"
    if not os.path.exists(sqlite_path):
        print(f"No SQLite database found at '{sqlite_path}'. Starting with empty PostgreSQL database.")
        setup_only = True
    else:
        print(f"Found SQLite database: {sqlite_path}")
        setup_only = False
        
        # Create backup
        if not backup_sqlite_database(sqlite_path):
            response = input("Failed to create backup. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Migration aborted.")
                return False
    
    # Step 2: Set up PostgreSQL
    print("\n--- Setting up PostgreSQL database ---")
    setup = PostgreSQLSetup()
    
    if not setup.create_database_if_not_exists():
        print("Failed to create PostgreSQL database.")
        return False
    
    if not setup.create_schema():
        print("Failed to create PostgreSQL schema.")
        return False
    
    # Step 3: Migrate data if SQLite database exists
    if not setup_only:
        print(f"\n--- Migrating data from SQLite ---")
        if not setup.migrate_from_sqlite(sqlite_path):
            print("Data migration failed.")
            return False
    
    # Step 4: Verify setup
    print("\n--- Verifying PostgreSQL setup ---")
    if not setup.verify_setup():
        print("PostgreSQL setup verification failed.")
        return False
    
    # Step 5: Show summary
    print("\n=== Migration Summary ===")
    try:
        config = DatabaseConfig()
        conn = psycopg2.connect(**config.get_postgres_params())
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM urls")
        url_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM urls GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        cursor.close()
        conn.close()
        
        print(f"✓ Total URLs in PostgreSQL: {url_count}")
        for status, count in status_counts.items():
            print(f"  - {status}: {count}")
        
        print(f"\n✓ PostgreSQL connection: {config.get_postgres_url()}")
        print("✓ Migration completed successfully!")
        
        if not setup_only:
            print(f"\nNote: Original SQLite database is still at '{sqlite_path}' and has been backed up.")
        
        return True
        
    except Exception as e:
        print(f"Error getting migration summary: {e}")
        return False


def install_dependencies():
    """Check and install required dependencies"""
    try:
        import psycopg2
        import dotenv
        print("✓ All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required dependencies:")
        print("  pip install -r requirements.txt")
        return False


if __name__ == "__main__":
    print("WebSpider PostgreSQL Migration Tool")
    print("===================================\n")
    
    # Check dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check .env file
    if not os.path.exists('.env'):
        print("Error: .env file not found.")
        print("Please create a .env file with PostgreSQL connection details.")
        sys.exit(1)
    
    # Run migration
    try:
        success = migrate_data()
        if success:
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Test the web spider with: python run_spider.py")
            print("2. Check the PostgreSQL database for your data")
            print("3. Update any custom scripts to use the new database")
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)