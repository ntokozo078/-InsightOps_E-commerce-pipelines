"""
Data Warehouse Loader
Loads cleaned data into SQLite star schema warehouse
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_PATH, CLEAN_DATA_DIR, WAREHOUSE_DIR


class WarehouseLoader:
    """Loads data into the star schema warehouse"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.conn = None
        
        # Ensure warehouse directory exists
        WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Connect to SQLite database"""
        print(f"📊 Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        print("✓ Connected successfully")
    
    def create_schema(self):
        """Create star schema tables"""
        print("\n🏗️  Creating star schema...")
        
        schema_file = WAREHOUSE_DIR / 'schema.sql'
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema creation
        self.conn.executescript(schema_sql)
        self.conn.commit()
        
        print("✓ Star schema created successfully")
    
    def load_dimensions(self):
        """Load dimension tables"""
        print("\n📥 Loading dimension tables...")
        
        # Load dim_date
        print("  ├─ Loading dim_date...")
        dim_date = pd.read_csv(CLEAN_DATA_DIR / 'dim_date.csv')
        dim_date.to_sql('dim_date', self.conn, if_exists='replace', index=False)
        print(f"     ✓ Loaded {len(dim_date):,} rows")
        
        # Load dim_customer
        print("  ├─ Loading dim_customer...")
        dim_customer = pd.read_csv(CLEAN_DATA_DIR / 'dim_customer.csv')
        dim_customer.to_sql('dim_customer', self.conn, if_exists='replace', index=False)
        print(f"     ✓ Loaded {len(dim_customer):,} rows")
        
        # Load dim_product
        print("  ├─ Loading dim_product...")
        dim_product = pd.read_csv(CLEAN_DATA_DIR / 'dim_product.csv')
        dim_product.to_sql('dim_product', self.conn, if_exists='replace', index=False)
        print(f"     ✓ Loaded {len(dim_product):,} rows")
        
        self.conn.commit()
    
    def load_fact_table(self):
        """Load fact table with foreign key mappings"""
        print("\n📥 Loading fact table...")
        
        # Load cleaned fact data
        fact_orders = pd.read_csv(CLEAN_DATA_DIR / 'fact_orders.csv')
        print(f"  ├─ Read {len(fact_orders):,} fact records")
        
        # Load dimension tables for key mapping
        dim_customer = pd.read_sql("SELECT customer_key, customer_id FROM dim_customer", self.conn)
        dim_product = pd.read_sql("SELECT product_key, product_id FROM dim_product", self.conn)
        dim_date = pd.read_sql("SELECT date_key, date FROM dim_date", self.conn)
        
        # Convert order_date to date_key format
        print("  ├─ Mapping foreign keys...")
        fact_orders['order_date'] = pd.to_datetime(fact_orders['order_date'])
        fact_orders['order_date_key'] = fact_orders['order_date'].dt.strftime('%Y%m%d').astype(int)
        
        # Map customer_id to customer_key
        fact_orders = fact_orders.merge(
            dim_customer[['customer_id', 'customer_key']], 
            on='customer_id', 
            how='left'
        )
        
        # Map product_id to product_key
        fact_orders = fact_orders.merge(
            dim_product[['product_id', 'product_key']], 
            on='product_id', 
            how='left'
        )
        
        # Select final columns for fact table
        fact_final = fact_orders[[
            'order_id', 'order_date_key', 'customer_key', 'product_key',
            'quantity', 'revenue', 'cost', 'profit', 'payment_status', 'channel'
        ]].copy()
        
        # Remove any rows with missing keys
        print("  ├─ Validating foreign key integrity...")
        before = len(fact_final)
        fact_final = fact_final.dropna(subset=['order_date_key', 'customer_key', 'product_key'])
        if before > len(fact_final):
            print(f"     ⚠ Removed {before - len(fact_final):,} rows with missing foreign keys")
        
        # Load to database
        print("  ├─ Inserting into database...")
        fact_final.to_sql('fact_orders', self.conn, if_exists='replace', index=False)
        print(f"     ✓ Loaded {len(fact_final):,} rows")
        
        self.conn.commit()
    
    def validate_warehouse(self):
        """Validate warehouse integrity"""
        print("\n✅ Validating warehouse...")
        
        # Check row counts
        tables = ['dim_date', 'dim_customer', 'dim_product', 'fact_orders']
        for table in tables:
            count = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {table}", self.conn).iloc[0]['cnt']
            print(f"  ├─ {table}: {count:,} rows")
        
        # Check for orphaned records
        print("\n  Checking foreign key integrity:")
        
        orphan_check = """
        SELECT COUNT(*) as cnt 
        FROM fact_orders f
        LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
        WHERE c.customer_key IS NULL
        """
        orphans = pd.read_sql(orphan_check, self.conn).iloc[0]['cnt']
        print(f"  ├─ Orphaned customer keys: {orphans}")
        
        orphan_check = """
        SELECT COUNT(*) as cnt 
        FROM fact_orders f
        LEFT JOIN dim_product p ON f.product_key = p.product_key
        WHERE p.product_key IS NULL
        """
        orphans = pd.read_sql(orphan_check, self.conn).iloc[0]['cnt']
        print(f"  ├─ Orphaned product keys: {orphans}")
        
        orphan_check = """
        SELECT COUNT(*) as cnt 
        FROM fact_orders f
        LEFT JOIN dim_date d ON f.order_date_key = d.date_key
        WHERE d.date_key IS NULL
        """
        orphans = pd.read_sql(orphan_check, self.conn).iloc[0]['cnt']
        print(f"  └─ Orphaned date keys: {orphans}")
        
        print("\n✅ Warehouse validation complete!")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print(f"\n📊 Database saved: {self.db_path}")
    
    def run(self):
        """Execute full warehouse loading process"""
        print("\n" + "=" * 60)
        print("INSIGHTOPS DATA WAREHOUSE LOADER")
        print("=" * 60)
        
        try:
            self.connect()
            self.create_schema()
            self.load_dimensions()
            self.load_fact_table()
            self.validate_warehouse()
            
            print("\n" + "=" * 60)
            print("✅ WAREHOUSE LOADING COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Warehouse loading failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.close()


if __name__ == "__main__":
    loader = WarehouseLoader()
    success = loader.run()
    sys.exit(0 if success else 1)
