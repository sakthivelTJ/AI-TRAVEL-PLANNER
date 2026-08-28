import os
import subprocess
import time
import requests
import traceback

def test_server():
    # Start the Flask app with empty API keys to simulate Render environment
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = ""
    env["TAVILY_API_KEY"] = ""
    env["VITE_SUPABASE_URL"] = ""
    env["VITE_SUPABASE_ANON_KEY"] = ""
    env["PORT"] = "5005"
    
    print("Starting server on port 5005 with cleared environment variables...")
    process = subprocess.Popen(
        [".venv\\Scripts\\python", "app.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the server to spin up
    time.sleep(3)
    
    try:
        print("Sending POST request to generate plan...")
        data = {
            "destination": "Paris",
            "days": "3",
            "people": "2",
            "accommodation": "mid-range",
            "activities": "sightseeing",
            "interests": "history, art",
            "budget": "medium",
            "budget_amount": "",
            "currency": "USD"
        }
        
        response = requests.post("http://127.0.0.1:5005/generate_plan", data=data, timeout=10)
        print("Response Status Code:", response.status_code)
        if response.status_code == 500:
            print("ERROR: Got 500 Internal Server Error!")
            print("Response text content:")
            print(response.text[:2000])
        else:
            print("SUCCESS! Status is", response.status_code)
            
    except Exception as e:
        print("Request failed:", e)
        traceback.print_exc()
        
    finally:
        print("Stopping Flask server...")
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=2)
            print("--- Server Stdout ---")
            print(stdout[:500])
            print("--- Server Stderr ---")
            print(stderr[:1000])
        except Exception as e:
            print("Could not get server logs:", e)

if __name__ == "__main__":
    test_server()
