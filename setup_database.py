"""
Database Setup Script
Automatically initializes the database if it doesn't exist
This is useful for cloud deployments where the database file is not included
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import DATABASE_PATH, WAREHOUSE_DIR
import subprocess


def database_exists():
    """Check if database exists"""
    return DATABASE_PATH.exists() and DATABASE_PATH.stat().st_size > 0


def setup_database():
    """Initialize database if it doesn't exist"""
    
    if database_exists():
        print(f"✅ Database already exists at {DATABASE_PATH}")
        return True
    
    print(f"⚠️  Database not found at {DATABASE_PATH}")
    print("🔧 Initializing database...")
    
    try:
        # Ensure warehouse directory exists
        WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run ETL pipeline
        print("📊 Running ETL pipeline...")
        etl_script = Path(__file__).parent / "scripts" / "etl_pipeline.py"
        
        if etl_script.exists():
            result = subprocess.run(
                [sys.executable, str(etl_script)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ ETL pipeline failed: {result.stderr}")
                return False
            
            print("✅ ETL pipeline completed")
        else:
            print(f"⚠️  ETL script not found at {etl_script}")
        
        # Load warehouse
        print("📦 Loading data warehouse...")
        load_script = WAREHOUSE_DIR / "load_warehouse.py"
        
        if load_script.exists():
            result = subprocess.run(
                [sys.executable, str(load_script)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Warehouse load failed: {result.stderr}")
                return False
            
            print("✅ Data warehouse loaded successfully")
        else:
            print(f"⚠️  Load script not found at {load_script}")
        
        # Verify database was created
        if database_exists():
            print(f"✅ Database initialized successfully at {DATABASE_PATH}")
            return True
        else:
            print("❌ Database initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during database setup: {str(e)}")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
