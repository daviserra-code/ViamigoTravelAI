#!/usr/bin/env python3
"""
Database schema inspection script
"""

import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def inspect_database_schema():
    """Inspect the comprehensive_attractions table schema"""
    print("🔍 Database Schema Inspection:")
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ No DATABASE_URL found")
        return
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'comprehensive_attractions'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        
        print(f"comprehensive_attractions table schema:")
        print(f"{'Column Name':<25} {'Data Type':<20} {'Nullable':<10} {'Default'}")
        print("-" * 70)
        for col in columns:
            print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3] or ''}")
        
        # Get sample data
        print(f"\nSample data (3 records):")
        cursor.execute("SELECT * FROM comprehensive_attractions LIMIT 3;")
        sample_data = cursor.fetchall()
        
        column_names = [desc[0] for desc in cursor.description]
        print(f"Columns: {', '.join(column_names)}")
        
        for i, row in enumerate(sample_data):
            print(f"\nRecord {i+1}:")
            for j, value in enumerate(row):
                print(f"  {column_names[j]}: {value}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database inspection failed: {e}")

if __name__ == "__main__":
    inspect_database_schema()