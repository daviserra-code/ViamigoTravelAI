#!/usr/bin/env python3
"""
Direct test of intelligent systems with database-first approach
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def test_intelligent_detail_handler():
    """Test the intelligent detail handler with database-first approach"""
    print("🧪 Testing Intelligent Detail Handler (Database-First)")
    
    try:
        from intelligent_detail_handler import IntelligentDetailHandler
        handler = IntelligentDetailHandler()
        
        # Test with famous attractions that should be in the database
        test_cases = [
            "Colosseo Roma",
            "Piazza Navona Roma", 
            "Fontana di Trevi Roma",
            "Palazzo dei Congressi Chiavari",
            "Duomo Milano"
        ]
        
        for test_case in test_cases:
            print(f"\n📍 Testing: {test_case}")
            result = handler.get_details(test_case)
            
            if result:
                print(f"✅ Name: {result.get('name', 'N/A')}")
                print(f"✅ City: {result.get('city', 'N/A')}")
                print(f"✅ Source: {result.get('source', 'N/A')}")
                print(f"✅ Confidence: {result.get('confidence', 'N/A')}")
                print(f"✅ Description: {result.get('description', 'N/A')[:100]}...")
            else:
                print("❌ No result returned")
                
    except Exception as e:
        print(f"❌ Error testing detail handler: {e}")

def test_intelligent_image_classifier():
    """Test the intelligent image classifier with database-first approach"""
    print("\n🧪 Testing Intelligent Image Classifier (Database-First)")
    
    try:
        from intelligent_image_classifier import IntelligentImageClassifier
        classifier = IntelligentImageClassifier()
        
        # Test with known attractions
        test_cases = [
            "Colosseo",
            "Piazza Navona",
            "Fontana di Trevi",
            "Duomo Milano",
            "Palazzo dei Congressi"
        ]
        
        for attraction in test_cases:
            print(f"\n🖼️  Testing: {attraction}")
            result = classifier.classify_image(attraction)
            
            if result:
                print(f"✅ Image URL: {result.get('image_url', 'N/A')}")
                print(f"✅ Source: {result.get('source', 'N/A')}")
                print(f"✅ Confidence: {result.get('confidence', 'N/A')}")
            else:
                print("❌ No result returned")
                
    except Exception as e:
        print(f"❌ Error testing image classifier: {e}")

if __name__ == "__main__":
    print("🔬 ViamigoTravelAI - Direct Intelligent Systems Test")
    print(f"Database URL configured: {bool(os.getenv('DATABASE_URL'))}")
    print("-" * 60)
    
    # Test detail handler
    test_intelligent_detail_handler()
    
    # Test image classifier  
    test_intelligent_image_classifier()
    
    print("\n✅ Direct intelligent systems testing complete!")