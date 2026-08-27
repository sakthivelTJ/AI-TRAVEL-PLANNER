import sys
sys.path.append('.')
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS
import json
import traceback

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
model_name = "gemini-2.5-flash"

prompt = """Create a travel plan for Paris. Respond ONLY in JSON with schema:
{"itinerary_markdown": "some markdown", "days": []}"""

try:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=DEFAULT_TEMPERATURE,
            max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
            response_mime_type="application/json"
        )
    )
    raw = response.text
    print("RAW OUTPUT:")
    print(raw[:500])
    print("---")
    
    try:
        parsed = json.loads(raw)
        print("PARSE SUCCESSFUL!")
        print("keys:", parsed.keys())
        print("itinerary_markdown type:", type(parsed.get('itinerary_markdown')))
    except Exception as e:
        print("PARSE FAILED!")
        traceback.print_exc()
except Exception as e:
    traceback.print_exc()
