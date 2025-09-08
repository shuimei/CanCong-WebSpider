import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DatabaseConfig:
    """Database configuration settings"""
    
    # PostgreSQL configuration from environment variables
    PG_HOST = os.getenv('PG_IP', 'localhost')
    PG_PORT = int(os.getenv('PG_PORT', 5432))
    PG_DATABASE = os.getenv('PG_DATABASE', 'webspider')
    PG_USERNAME = os.getenv('PG_USERNAME', 'postgres')
    PG_PASSWORD = os.getenv('PG_PASSWORD', '')
    
    @classmethod
    def get_postgres_url(cls):
        """Get PostgreSQL connection URL"""
        return f"postgresql://{cls.PG_USERNAME}:{cls.PG_PASSWORD}@{cls.PG_HOST}:{cls.PG_PORT}/{cls.PG_DATABASE}"
    
    @classmethod
    def get_postgres_params(cls):
        """Get PostgreSQL connection parameters as dictionary"""
        return {
            'host': cls.PG_HOST,
            'port': cls.PG_PORT,
            'database': cls.PG_DATABASE,
            'user': cls.PG_USERNAME,
            'password': cls.PG_PASSWORD
        }


class AppConfig:
    """Application configuration settings"""
    
    # Web scraping settings
    WEBPAGES_DIR = os.getenv('WEBPAGES_DIR', 'webpages')
    
    # File storage settings
    MAX_FILENAME_LENGTH = 200
    
    # Crawling settings
    DEFAULT_CRAWL_DELAY = 2
    DEFAULT_CONCURRENT_REQUESTS = 4