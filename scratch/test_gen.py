import sys
sys.path.append('.')
from app import generate_travel_plan

travel_params = {
    'destination': 'Paris',
    'days': '3',
    'people': '2',
    'accommodation': 'mid-range',
    'activities': 'sightseeing',
    'interests': 'culture, food',
    'budget': 'medium'
}

print("Running generate_travel_plan...")
result = generate_travel_plan(travel_params)
print("Keys in result:", result.keys())
print("Content starts with:")
print(result['content'][:500])
