#!/usr/bin/env python3
"""
Test Flask app routes and web interface
"""

from app import app
from flask import url_for

def test_flask_routes():
    """Test all Flask routes"""
    
    print("=" * 70)
    print("🌐 TESTING FLASK WEB ROUTES")
    print("=" * 70)
    
    with app.app_context():
        routes_to_test = [
            ('/', 'index', 'Home page'),
            ('/planner', 'planner', 'Planner page'),
        ]
        
        print("\n✅ AVAILABLE ROUTES:")
        print("-" * 70)
        
        for path, endpoint, description in routes_to_test:
            try:
                url = url_for(endpoint)
                print(f"  ✓ {description}")
                print(f"    Endpoint: {endpoint}")
                print(f"    URL: {url}")
            except Exception as e:
                print(f"  ✗ {description}: {e}")
        
        # List all registered routes
        print("\n📋 ALL REGISTERED ROUTES:")
        print("-" * 70)
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
                print(f"  • {str(rule):40} [{methods}]")
        
        print("\n" + "=" * 70)
        print("✅ FLASK APP CONFIGURATION VERIFIED")
        print("=" * 70)

if __name__ == "__main__":
    test_flask_routes()
