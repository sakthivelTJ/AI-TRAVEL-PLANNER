import subprocess
import time
import requests
import os

env = os.environ.copy()
env["GEMINI_API_KEY"] = ""  # empty key to trigger fallback
env["TAVILY_API_KEY"] = ""
env["VITE_SUPABASE_URL"] = ""
env["VITE_SUPABASE_ANON_KEY"] = ""
env["PORT"] = "5005"

process = subprocess.Popen(
    [".venv\\Scripts\\python", "app.py"],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(3)

try:
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
    
    response = requests.post("http://127.0.0.1:5005/generate_plan", data=data, timeout=40)
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/plan_output.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Plan output HTML saved to scratch/plan_output.html")
    
finally:
    process.terminate()
