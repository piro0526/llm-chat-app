#!/usr/bin/env python3
"""
Database initialization script for the LLM Chat App.
This script handles database creation, migration, and health checks.
"""

import os
import sys
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from config import settings
from database import Base, engine, test_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_db(max_retries=60, retry_interval=2):
    """Wait for database to be available"""
    logger.info("Waiting for database to be available...")
    
    for attempt in range(max_retries):
        try:
            if test_connection():
                logger.info("Database is available!")
                return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_interval)
    
    logger.error("Database failed to become available after maximum retries")
    return False


def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database to create our app database
        db_url = settings.effective_database_url
        db_name = db_url.split('/')[-1]
        postgres_url = db_url.rsplit('/', 1)[0] + '/postgres'
        
        logger.info(f"Checking if database '{db_name}' exists...")
        
        postgres_engine = create_engine(postgres_url)
        with postgres_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                logger.info(f"Creating database '{db_name}'...")
                # Create database
                conn.execute(text("COMMIT"))
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
                
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


def create_tables():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    try:
        # Wait for database to be available
        if not wait_for_db():
            sys.exit(1)
        
        # Create database if it doesn't exist
        create_database_if_not_exists()
        
        # Create tables
        create_tables()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()