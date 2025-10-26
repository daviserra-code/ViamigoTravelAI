#!/usr/bin/env python3
"""
Quick test script to verify database environment and connection
"""

import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def test_env_vars():
    """Test if environment variables are loaded"""
    print("🔍 Environment Variables Test:")
    
    database_url = os.getenv('DATABASE_URL')
    openai_key = os.getenv('OPENAI_API_KEY')
    apify_token = os.getenv('APIFY_API_TOKEN')
    
    print(f"DATABASE_URL: {'✅ Found' if database_url else '❌ Missing'}")
    print(f"OPENAI_API_KEY: {'✅ Found' if openai_key else '❌ Missing'}")
    print(f"APIFY_API_TOKEN: {'✅ Found' if apify_token else '❌ Missing'}")
    
    if database_url:
        print(f"DATABASE_URL preview: {database_url[:30]}...")
    
    return database_url

def test_database_connection(db_url):
    """Test PostgreSQL database connection"""
    print("\n🔍 Database Connection Test:")
    
    if not db_url:
        print("❌ No DATABASE_URL found - cannot test connection")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL connected: {version[0][:50]}...")
        
        # Test if comprehensive_attractions table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'comprehensive_attractions'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"comprehensive_attractions table: {'✅ Exists' if table_exists else '❌ Missing'}")
        
        if table_exists:
            # Count records
            cursor.execute("SELECT COUNT(*) FROM comprehensive_attractions;")
            count = cursor.fetchone()[0]
            print(f"Records in comprehensive_attractions: {count}")
            
            # Sample some data
            cursor.execute("SELECT name, city, attraction_type FROM comprehensive_attractions LIMIT 3;")
            samples = cursor.fetchall()
            print("Sample data:")
            for sample in samples:
                print(f"  - {sample[0]} ({sample[1]}, {sample[2]})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_intelligent_handler_import():
    """Test if intelligent handler can be imported and initialized"""
    print("\n🔍 Intelligent Handler Import Test:")
    
    try:
        from intelligent_detail_handler import IntelligentDetailHandler
        handler = IntelligentDetailHandler()
        print("✅ IntelligentDetailHandler imported and initialized successfully")
        return True
    except Exception as e:
        print(f"❌ IntelligentDetailHandler import failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ViamigoTravelAI - Database Environment Test\n")
    
    # Test environment variables
    db_url = test_env_vars()
    
    # Test database connection
    db_connected = test_database_connection(db_url)
    
    # Test intelligent handler import
    handler_imported = test_intelligent_handler_import()
    
    print(f"\n📊 Test Summary:")
    print(f"Environment Variables: {'✅ OK' if db_url else '❌ FAIL'}")
    print(f"Database Connection: {'✅ OK' if db_connected else '❌ FAIL'}")
    print(f"Intelligent Handler: {'✅ OK' if handler_imported else '❌ FAIL'}")
    
    if db_url and db_connected:
        print("\n🎉 Database is properly configured and connected!")
        print("The intelligent systems should now use database-first approach.")
    else:
        print("\n⚠️  Database configuration issues detected.")
        print("Intelligent systems will fall back to Apify integration.")