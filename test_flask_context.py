#!/usr/bin/env python3
"""
Test intelligent systems with proper Flask app context
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def test_intelligent_systems_with_flask_context():
    """Test intelligent systems with proper Flask application context"""
    print("🧪 Testing Intelligent Systems with Flask App Context")
    
    try:
        # Import Flask app
        from flask_app import app
        
        # Test with proper Flask app context
        with app.app_context():
            print("✅ Flask app context established")
            
            # Test detail handler
            print("\n📍 Testing Detail Handler:")
            from intelligent_detail_handler import IntelligentDetailHandler
            handler = IntelligentDetailHandler()
            
            test_cases = ["Colosseo Roma", "Piazza Navona Roma"]
            
            for test_case in test_cases:
                print(f"\n🔍 Testing: {test_case}")
                result = handler.get_details(test_case)
                
                if result:
                    print(f"✅ Name: {result.get('name', 'N/A')}")
                    print(f"✅ City: {result.get('city', 'N/A')}")  
                    print(f"✅ Source: {result.get('source', 'N/A')}")
                    print(f"✅ Confidence: {result.get('confidence', 'N/A')}")
                    
                    if result.get('source') == 'database':
                        print("🎉 SUCCESS: Using database-first approach!")
                    elif result.get('source') == 'apify':
                        print("⚠️  Using Apify fallback (database query may have failed)")
                    else:
                        print(f"ℹ️  Using {result.get('source')} approach")
                else:
                    print("❌ No result returned")
            
            # Test image classifier
            print("\n🖼️  Testing Image Classifier:")
            from intelligent_image_classifier import IntelligentImageClassifier
            classifier = IntelligentImageClassifier()
            
            test_images = ["Colosseo", "Piazza Navona"]
            
            for attraction in test_images:
                print(f"\n🔍 Testing: {attraction}")
                result = classifier.classify_image(attraction)
                
                if result:
                    print(f"✅ Image URL: {result.get('image_url', 'N/A')}")
                    print(f"✅ Source: {result.get('source', 'N/A')}")
                    
                    if result.get('source') == 'database':
                        print("🎉 SUCCESS: Using database-first approach!")
                    elif result.get('source') == 'apify':
                        print("⚠️  Using Apify fallback")
                    else:
                        print(f"ℹ️  Using {result.get('source')} approach")
                else:
                    print("❌ No result returned")
                    
    except Exception as e:
        print(f"❌ Error testing with Flask context: {e}")

if __name__ == "__main__":
    print("🔬 ViamigoTravelAI - Flask Context Test\n")
    test_intelligent_systems_with_flask_context()
    print("\n✅ Flask context testing complete!")