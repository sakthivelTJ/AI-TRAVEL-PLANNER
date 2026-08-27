#!/usr/bin/env python
"""Test script to debug travel plan generation"""

import traceback
import time
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

params = {
    'destination': 'Paris',
    'days': '2',
    'people': '2',
    'accommodation': 'mid-range',
    'activities': 'sightseeing',
    'interests': 'art, food',
    'budget': 'medium'
}

print('Testing Gemini API directly...')
print('-' * 50)

# Configure Gemini
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
model_name = "gemini-2.5-flash"

# Build a simple prompt to test with sanitized input
# Validate and sanitize numeric inputs
try:
    days = int(params['days'])
    people = int(params['people'])
except (ValueError, TypeError):
    days = 2
    people = 2

# Create prompt with validated inputs only
prompt = f"""Create a detailed {days}-day travel itinerary for {params['destination']} in markdown format.

# {params['destination']} - {days} Day Travel Plan

## Trip Overview
- Destination: {params['destination']}
- Duration: {days} days
- Travelers: {people} people
- Budget: {params['budget']}
- Interests: {params['interests']}

## Day-by-Day Itinerary

Create a detailed itinerary for EACH of the {days} days. For each day include:
- A theme or focus for the day.
- Morning, Afternoon, and Evening sections with specific activities, locations, and tips.
- Recommendations for meals (lunch and dinner).

Format each day as:
### Day [number]: [Theme/Focus]
**Morning (8:00 AM - 12:00 PM)**
- Activity: [Specific location/attraction]

**Afternoon (12:00 PM - 6:00 PM)**
- Lunch: [Restaurant recommendation]
- Activity: [Specific location]

**Evening (6:00 PM - 10:00 PM)**
- Dinner: [Restaurant recommendation]
- Evening activity: [Specific location or experience]

Create a complete itinerary for all {days} days."""

print('Sending request to Gemini API...')
start_time = time.time()

try:
    if client is None:
        print("GEMINI_API_KEY is not configured. Skipping API test.")
    else:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
        )
        elapsed = time.time() - start_time
        
        print(f'[OK] API Response received in {elapsed:.2f} seconds')
        
        # Validate response and extract text safely
        if response and hasattr(response, 'text') and response.text:
            response_text = response.text
            print(f'Response length: {len(response_text)} characters')
            
            # A more robust check for the itinerary structure
            has_day_1 = "Day 1" in response_text
            has_day_2 = "Day 2" in response_text
            
            print(f'[OK] Contains "Day 1": {has_day_1}')
            print(f'[OK] Contains "Day 2": {has_day_2}')
            
            if has_day_1 and has_day_2:
                print("[SUCCESS] SUCCESS: Itinerary seems to be generated correctly.")
                print(f"\nContent preview (first 500 chars):\n{response_text[:500]}")
            else:
                print("[FAIL] Unexpected response format. Itinerary sections might be missing.")
                print(f"Full Response:\n{response_text}")
        else:
            print("[FAIL] Invalid response received from API")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f'[ERROR] Exception occurred after {elapsed:.2f} seconds')
    print(f'Error: {e}')
    traceback.print_exc()
