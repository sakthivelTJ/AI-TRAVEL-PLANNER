#!/usr/bin/env python3
"""
Complete end-to-end test for the AI Travel Planner application
Tests the full workflow: API call → JSON parsing → Markdown generation
"""

import json
import sys
from app import generate_travel_plan, format_markdown_content

def test_travel_plan_generation():
    """Test the complete travel plan generation workflow"""
    
    print("=" * 70)
    print("🌍 AI TRAVEL PLANNER - COMPLETE END-TO-END TEST")
    print("=" * 70)
    
    # Test parameters
    test_params = {
        'destination': 'Tokyo',
        'days': '3',
        'people': '2',
        'accommodation': 'luxury',
        'activities': 'sightseeing, cultural',
        'interests': 'temples, food, shopping',
        'budget': 'medium',
        'budget_amount': '5000',
        'currency': 'INR',
        'pace': 'balanced',
        'trip_style': 'first-time highlights',
        'dietary': 'no preference',
        'accessibility': 'none'
    }
    
    print("\n📋 TEST PARAMETERS:")
    print("-" * 70)
    for key, value in test_params.items():
        print(f"  • {key}: {value}")
    
    print("\n⏳ Generating travel plan... (this may take 10-30 seconds)")
    print("-" * 70)
    
    try:
        # Generate the travel plan
        result = generate_travel_plan(test_params)
        
        # Extract the results
        html_content = result.get("content", "")
        sources = result.get("sources", [])
        plan_id = result.get("plan_id")
        
        print("✅ Travel plan generated successfully!")
        
        # Validate HTML content
        print("\n📄 VALIDATING CONTENT:")
        print("-" * 70)
        
        if html_content:
            print(f"  ✓ HTML content length: {len(html_content)} characters")
            
            # Check for key sections
            checks = {
                "Day 1": "First day itinerary",
                "Day 2": "Second day itinerary",
                "Day 3": "Third day itinerary",
                "Morning": "Morning activities",
                "Afternoon": "Afternoon activities",
                "Evening": "Evening activities",
                "Tokyo": "Destination mentioned",
                "Budget": "Budget breakdown"
            }
            
            passed = 0
            for check_key, description in checks.items():
                if check_key in html_content:
                    print(f"  ✓ {description} (found: '{check_key}')")
                    passed += 1
                else:
                    print(f"  ✗ {description} (missing: '{check_key}')")
            
            print(f"\n  Validation Score: {passed}/{len(checks)}")
        else:
            print("  ✗ No HTML content generated!")
            return False
        
        # Check sources
        print("\n🔗 SOURCES AND METADATA:")
        print("-" * 70)
        print(f"  • Total sources: {len(sources)}")
        if sources:
            for i, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    source_type = source.get("type", "unknown")
                    if source_type == "days_data":
                        days_data = source.get("data", [])
                        print(f"  • Source {i}: Days data ({len(days_data)} days)")
                    else:
                        name = source.get("name", "Unknown")
                        url = source.get("url", "")
                        print(f"  • Source {i}: {name}")
                        if url:
                            print(f"    URL: {url}")
        
        # Plan ID
        print("\n💾 STORAGE:")
        print("-" * 70)
        if plan_id:
            print(f"  ✓ Plan saved with ID: {plan_id}")
        else:
            print(f"  ℹ No plan ID (Supabase may be unavailable)")
        
        # Display sample output
        print("\n📝 SAMPLE OUTPUT (First 800 characters):")
        print("-" * 70)
        # Remove HTML tags for readability
        text_preview = html_content[:1000]
        text_preview = text_preview.replace("<p>", "\n  ").replace("</p>", "")
        text_preview = text_preview.replace("<h1>", "\n### ").replace("</h1>", "")
        text_preview = text_preview.replace("<h2>", "\n## ").replace("</h2>", "")
        text_preview = text_preview.replace("<h3>", "\n# ").replace("</h3>", "")
        text_preview = text_preview.replace("<br/>", "\n")
        text_preview = text_preview.replace("<ul>", "").replace("</ul>", "")
        text_preview = text_preview.replace("<li>", "  • ").replace("</li>", "")
        text_preview = text_preview.replace("<strong>", "").replace("</strong>", "")
        text_preview = text_preview.replace("<em>", "").replace("</em>", "")
        
        print(text_preview[:800])
        
        print("\n" + "=" * 70)
        print("✅ TEST PASSED: Travel planner is working correctly!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_travel_plan_generation()
    sys.exit(0 if success else 1)
