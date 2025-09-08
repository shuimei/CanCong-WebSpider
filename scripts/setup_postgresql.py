"""
PostgreSQL database schema and migration utilities for WebSpider
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlite3
import os
from datetime import datetime
from webspider.config import DatabaseConfig


class PostgreSQLSetup:
    """PostgreSQL database setup and migration utilities"""
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist"""
        try:
            # Connect to PostgreSQL server (to 'postgres' database)
            conn_params = self.config.get_postgres_params()
            conn_params['database'] = 'postgres'  # Connect to default postgres database
            
            conn = psycopg2.connect(**conn_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                          (self.config.PG_DATABASE,))
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f'CREATE DATABASE "{self.config.PG_DATABASE}"')
                print(f"Database '{self.config.PG_DATABASE}' created successfully.")
            else:
                print(f"Database '{self.config.PG_DATABASE}' already exists.")
            
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.Error as e:
            print(f"Error creating database: {e}")
            return False
    
    def create_schema(self):
        """Create the database schema"""
        try:
            conn = psycopg2.connect(**self.config.get_postgres_params())
            cursor = conn.cursor()
            
            # Create URLs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    source_url TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    depth INTEGER DEFAULT 0,
                    title TEXT,
                    html_file_path TEXT,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    crawled_time TIMESTAMP,
                    error_message TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_url ON urls(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_depth ON urls(depth)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_urls_created_time ON urls(created_time)')
            
            # Create pages table for storing page content metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    id SERIAL PRIMARY KEY,
                    url_id INTEGER REFERENCES urls(id) ON DELETE CASCADE,
                    content_hash VARCHAR(64),
                    content_size INTEGER,
                    content_type VARCHAR(100),
                    extracted_urls_count INTEGER DEFAULT 0,
                    processing_time_ms INTEGER,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for pages table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_url_id ON pages(url_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON pages(content_hash)')
            
            # Create crawl_stats table for tracking statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawl_stats (
                    id SERIAL PRIMARY KEY,
                    date DATE DEFAULT CURRENT_DATE,
                    urls_added INTEGER DEFAULT 0,
                    urls_crawled INTEGER DEFAULT 0,
                    urls_failed INTEGER DEFAULT 0,
                    pages_saved INTEGER DEFAULT 0,
                    total_processing_time_ms BIGINT DEFAULT 0,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create unique index for daily stats
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_crawl_stats_date ON crawl_stats(date)')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("PostgreSQL schema created successfully.")
            return True
            
        except psycopg2.Error as e:
            print(f"Error creating schema: {e}")
            return False
    
    def migrate_from_sqlite(self, sqlite_db_path='spider_urls.db'):
        """Migrate data from SQLite to PostgreSQL"""
        if not os.path.exists(sqlite_db_path):
            print(f"SQLite database '{sqlite_db_path}' not found. Skipping migration.")
            return True
        
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_db_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to PostgreSQL
            pg_conn = psycopg2.connect(**self.config.get_postgres_params())
            pg_cursor = pg_conn.cursor()
            
            # Get all data from SQLite
            sqlite_cursor.execute('''
                SELECT url, source_url, status, depth, title, html_file_path, 
                       created_time, crawled_time, error_message 
                FROM urls
            ''')
            
            rows = sqlite_cursor.fetchall()
            
            # Insert data into PostgreSQL
            migrated_count = 0
            for row in rows:
                try:
                    pg_cursor.execute('''
                        INSERT INTO urls (url, source_url, status, depth, title, 
                                        html_file_path, created_time, crawled_time, error_message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    ''', row)
                    
                    if pg_cursor.rowcount > 0:
                        migrated_count += 1
                        
                except psycopg2.Error as e:
                    print(f"Error migrating row {row[0]}: {e}")
                    continue
            
            pg_conn.commit()
            
            # Close connections
            sqlite_cursor.close()
            sqlite_conn.close()
            pg_cursor.close()
            pg_conn.close()
            
            print(f"Migration completed. {migrated_count} records migrated from SQLite to PostgreSQL.")
            return True
            
        except Exception as e:
            print(f"Error during migration: {e}")
            return False
    
    def verify_setup(self):
        """Verify that the PostgreSQL setup is working correctly"""
        try:
            conn = psycopg2.connect(**self.config.get_postgres_params())
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute("SELECT COUNT(*) FROM urls")
            url_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM pages")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM crawl_stats")
            stats_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"PostgreSQL setup verification successful:")
            print(f"  - URLs table: {url_count} records")
            print(f"  - Pages table: {page_count} records") 
            print(f"  - Stats table: {stats_count} records")
            
            return True
            
        except psycopg2.Error as e:
            print(f"PostgreSQL setup verification failed: {e}")
            return False


def main():
    """Main function to set up PostgreSQL database"""
    print("Setting up PostgreSQL database for WebSpider...")
    
    setup = PostgreSQLSetup()
    
    # Step 1: Create database if it doesn't exist
    if not setup.create_database_if_not_exists():
        print("Failed to create database. Exiting.")
        return False
    
    # Step 2: Create schema
    if not setup.create_schema():
        print("Failed to create schema. Exiting.")
        return False
    
    # Step 3: Migrate data from SQLite if it exists
    if not setup.migrate_from_sqlite():
        print("Failed to migrate data from SQLite.")
        return False
    
    # Step 4: Verify setup
    if not setup.verify_setup():
        print("Setup verification failed.")
        return False
    
    print("PostgreSQL setup completed successfully!")
    return True


if __name__ == '__main__':
    main()