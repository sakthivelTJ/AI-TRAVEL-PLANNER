#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.getcwd(), '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"[TEST] API Key loaded: {GEMINI_API_KEY[:20]}..." if GEMINI_API_KEY else "[TEST] NO API KEY FOUND")
print(f"[TEST] Current working directory: {os.getcwd()}")

# Test Gemini API connection
try:
    from google import genai
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("[TEST] Gemini client created successfully")
    
    # Try to generate content
    print("[TEST] Attempting to generate content with gemini-2.0-flash...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say 'Hello World' in one sentence",
        config={
            "temperature": 0.7,
            "max_output_tokens": 100
        }
    )
    print(f"[TEST] SUCCESS! Response: {response.text}")
    
except Exception as e:
    print(f"[TEST] ERROR: {e}")
    print(f"[TEST] Error type: {type(e).__name__}")
    print(f"[TEST] Full traceback:\n{traceback.format_exc()}")

print("\n" + "="*50)
print("[TEST] Testing with gemini-2.5-flash...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'Hello World' in one sentence",
        config={
            "temperature": 0.7,
            "max_output_tokens": 100
        }
    )
    print(f"[TEST] SUCCESS with gemini-2.5-flash! Response: {response.text}")
except Exception as e:
    print(f"[TEST] ERROR with gemini-2.5-flash: {e}")
    print(f"[TEST] Error type: {type(e).__name__}")
