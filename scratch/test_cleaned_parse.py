import sys
sys.path.append('.')
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS
import json
import re
import traceback

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
model_name = "gemini-2.5-flash"

prompt = """Create a 2-day travel plan for Paris. Respond ONLY in JSON with the following schema:
{
  "itinerary_markdown": "detailed markdown containing headers and lists",
  "days": [
    {
      "day": 1,
      "stops": [
        {
          "name": "Eiffel Tower",
          "description": "Visit Eiffel Tower",
          "time": "09:00 AM",
          "transport_to_next": "WALKING"
        }
      ]
    }
  ]
}"""

try:
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is missing.")
        
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
    print(raw[:400])
    print("---")
    
    cleaned_text = raw.strip()
    # Remove markdown code fences if present in the response
    code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_text, re.DOTALL)
    if code_block_match:
        print("DETECTED CODE FENCES! Cleaning...")
        cleaned_text = code_block_match.group(1).strip()
        
    try:
        parsed = json.loads(cleaned_text)
        print("PARSE SUCCESSFUL!")
        print("keys:", list(parsed.keys()))
        print("itinerary_markdown length:", len(parsed.get('itinerary_markdown', '')))
        print("days count:", len(parsed.get('days', [])))
    except Exception as e:
        print("PARSE FAILED!")
        traceback.print_exc()
except Exception as e:
    traceback.print_exc()
