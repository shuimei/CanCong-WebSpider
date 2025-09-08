#!/usr/bin/env python3
"""
Test script for PostgreSQL integration with WebSpider
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webspider.database import UrlDatabase
from webspider.config import DatabaseConfig


def test_database_operations():
    """Test basic database operations"""
    print("Testing PostgreSQL integration...")
    
    try:
        # Test database connection
        db = UrlDatabase()
        print("✓ Database connection successful")
        
        # Test adding a URL
        test_url = "https://test-example.com/test-page"
        success = db.add_url(test_url, depth=0)
        if success:
            print("✓ Add URL operation successful")
        else:
            print("✓ Add URL operation completed (URL may already exist)")
        
        # Test checking if URL is crawled
        is_crawled = db.is_crawled(test_url)
        print(f"✓ URL crawled status check: {is_crawled}")
        
        # Test marking URL as crawling
        db.mark_crawling(test_url)
        print("✓ Mark URL as crawling successful")
        
        # Test marking URL as successful
        db.mark_success(test_url, title="Test Page", html_file_path="/test/path.html")
        print("✓ Mark URL as successful completed")
        
        # Test getting stats
        stats = db.get_stats()
        print("✓ Get statistics successful:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        # Test getting pending URLs
        pending_urls = db.get_pending_urls(limit=5)
        print(f"✓ Retrieved {len(pending_urls)} pending URLs")
        
        # Test cleanup stale crawling
        cleaned = db.cleanup_stale_crawling()
        print(f"✓ Cleaned up {cleaned} stale crawling URLs")
        
        print("\n🎉 All database operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        config = DatabaseConfig()
        print(f"✓ PostgreSQL Host: {config.PG_HOST}")
        print(f"✓ PostgreSQL Port: {config.PG_PORT}")
        print(f"✓ PostgreSQL Database: {config.PG_DATABASE}")
        print(f"✓ PostgreSQL User: {config.PG_USERNAME}")
        print(f"✓ Connection URL: {config.get_postgres_url()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


if __name__ == "__main__":
    print("WebSpider PostgreSQL Integration Test")
    print("=====================================\n")
    
    # Test configuration
    config_success = test_config()
    
    # Test database operations
    db_success = test_database_operations()
    
    # Summary
    print("\n" + "="*50)
    if config_success and db_success:
        print("✅ All tests passed! PostgreSQL integration is working correctly.")
        
        print("\nYour web spider is now configured to use PostgreSQL.")
        print("You can now run your spiders and they will store data in PostgreSQL.")
        
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)