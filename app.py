from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from google import genai
from google.genai import types
import requests
import json
import os
from datetime import datetime
from markupsafe import Markup
import markdown
import bleach
from config import (
    GEMINI_API_KEY, TAVILY_API_KEY, DEFAULT_TEMPERATURE,
    DEFAULT_MAX_OUTPUT_TOKENS, SUPABASE_URL, SUPABASE_KEY, SECRET_KEY
)
from supabase import create_client, Client
import traceback

app = Flask(__name__)
app.secret_key = SECRET_KEY  # Stable key so sessions survive restarts

# Configure Supabase (env already loaded via config import)
supabase: Client | None = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Configure Gemini API
client = (
    genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=60000),
    )
    if GEMINI_API_KEY
    else None
)

MARKDOWN_EXTENSIONS = ['extra', 'nl2br', 'sane_lists', 'fenced_code', 'tables']

# Fallback content in case API fails
fallback_content = {
    "content": 
        """
        # Travel Plan
            
        ## Overview
        We're experiencing technical difficulties generating your personalized itinerary. Here's a general guide to help you start planning:

        ## Day-by-Day Itinerary

        ### Day 1: Arrival & Orientation
        **Morning**
        - Arrive at destination
        - Check into accommodation
        - Get oriented with the area

        **Afternoon**
        - Explore nearby attractions
        - Visit local markets or shopping areas
        - Try local cuisine for lunch

        **Evening**
        - Dinner at a recommended restaurant
        - Evening stroll or rest

        ### Day 2: Main Attractions
        **Morning**
        - Visit top-rated tourist attractions
        - Take guided tours if available

        **Afternoon**
        - Continue sightseeing
        - Lunch at local eatery
        - Visit museums or cultural sites

        **Evening**
        - Dinner and local entertainment
        - Experience nightlife or cultural shows

        ### Day 3: Local Experiences
        **Morning**
        - Explore local neighborhoods
        - Visit markets and shops

        **Afternoon**
        - Try local activities
        - Lunch at authentic restaurant
        - Visit hidden gems

        **Evening**
        - Farewell dinner
        - Prepare for departure

        ## Planning Tips
        - Book accommodations in advance
        - Research local customs and etiquette
        - Check travel advisories
        - Make a list of must-see attractions
        - Consider local transportation options

        ## Budget Considerations
        - Accommodation: Varies by preference
        - Meals: Budget accordingly
        - Activities: Research costs in advance
        - Transportation: Factor in local travel

        ## Safety and Preparation
        - Keep emergency contact numbers handy
        - Make copies of important documents
        - Check travel insurance options
        - Research local healthcare facilities
        - Stay updated on local conditions

        Please try again later for a more detailed, personalized travel plan.""",
            "sources": [
                {
                    "name": "Travel Advisory",
                    "url": "https://travel.state.gov/content/travel.html"
                }
            ]
}

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'blockquote', 'hr', 'br',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'strong', 'em', 'del'
]
ALLOWED_ATTRS = {**bleach.sanitizer.ALLOWED_ATTRIBUTES, 'a': ['href', 'title', 'rel'], 'td': ['align'], 'th': ['align']}

def format_markdown_content(content):
    """Format the content with proper markdown structure"""
    raw_html = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS)
    return bleach.clean(raw_html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)

def itinerary_json_to_markdown(response_json, destination, days):
    """Normalize Gemini's structured itinerary response for the plan view."""
    itinerary = response_json.get('day_by_day_itinerary', [])
    if not isinstance(itinerary, list):
        return ''

    lines = [f"# {destination} - {days} Day Travel Plan", '', '## Day-by-Day Itinerary', '']
    for day_item in itinerary:
        if not isinstance(day_item, dict):
            continue
        day_number = day_item.get('day', len(lines))
        theme = day_item.get('theme_focus', 'Travel highlights')
        lines.extend([f"### Day {day_number}: {theme}"])
        for period in ('morning', 'afternoon', 'evening'):
            details = day_item.get(period, {})
            if not isinstance(details, dict):
                continue
            time = details.get('time', '')
            heading = period.capitalize() + (f" ({time})" if time else '')
            lines.extend([f"**{heading}**"])
            for label, value in details.items():
                if label == 'time' or not value:
                    continue
                lines.append(f"- {label.replace('_', ' ').capitalize()}: {value}")
            lines.append('')

    return '\n'.join(lines).strip()
def search_travel_info(query, destination):
    """Enhanced Tavily API to search for travel information"""
    if not TAVILY_API_KEY:
        print("[DEBUG] Tavily API key is missing; skipping travel research")
        return []

    url = "https://api.tavily.com/search"
    
    # Craft more specific search queries for better results
    search_queries = [
        f"top attractions in {destination} travel guide",
        f"{destination} local restaurants and cuisine guide",
        f"where to stay in {destination} best neighborhoods",
        f"{destination} travel tips local customs",
        f"{destination} transportation options for tourists"
    ]
    
    all_results = []
    
    # Make multiple targeted searches
    for search_query in search_queries:
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": search_query,
            "search_depth": "advanced",
            "include_domains": [
                "tripadvisor.com", "lonelyplanet.com", "timeout.com", 
                "booking.com", "airbnb.com", "wikitravel.org", 
                "travel.state.gov", "cntraveler.com", "atlasobscura.com"
            ],
            "max_results": 3
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            results = response.json()
            if results and "results" in results:
                all_results.extend(results["results"])
        except requests.exceptions.RequestException as e:
            print(f"Tavily API Error for query '{search_query}': {e}")
    
    # Deduplicate results based on URL
    unique_results = {}
    for result in all_results:
        if result["url"] not in unique_results:
            unique_results[result["url"]] = result
    
    return list(unique_results.values())

def save_travel_plan(travel_params, content, sources):
    """Save the travel plan to Supabase"""
    if supabase is None:
        return None
    try:
        data = {
            "destination": travel_params['destination'],
            "days": int(travel_params['days']),
            "people": int(travel_params['people']),
            "accommodation": travel_params['accommodation'],
            "activities": travel_params['activities'],
            "interests": travel_params['interests'],
            "budget": travel_params.get('budget', 'medium'),
            "content": content,
            "sources": sources
        }
        
        # Associate user_id if user is authenticated in the session
        if 'user' in session:
            data['user_id'] = session['user']['id']
             
        result = supabase.table('travel_plans').insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error saving travel plan to Supabase: {e}")
        return None


def get_travel_plan(plan_id):
    """Retrieve a travel plan from Supabase"""
    if supabase is None:
        return None
    try:
        result = supabase.table('travel_plans').select("*").eq('id', plan_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error retrieving travel plan: {e}")
        return None
def format_date(date_str):
    """Convert string date to formatted date string"""
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y")
        return None
    except Exception:
        return None

def generate_travel_plan(travel_params):
    """Generate a travel plan using Gemini API with enhanced prompt"""
    import re
    
    # Sanitize and validate all user inputs
    def sanitize_input(value, max_length=100):
        """Sanitize user input to prevent prompt injection"""
        if not isinstance(value, str):
            value = str(value)
        # Remove potentially dangerous characters and limit length
        value = value.strip()[:max_length]
        # Remove newlines and special prompt injection patterns
        value = value.replace('\n', ' ').replace('\r', ' ')
        return value
    
    # Validate numeric inputs
    def validate_number(value, min_val=1, max_val=365):
        """Validate numeric inputs are within acceptable range"""
        try:
            # Extract digits, e.g. "15+" -> "15"
            sanitized = re.sub(r'\D', '', str(value))
            num = int(sanitized) if sanitized else min_val
            return max(min_val, min(num, max_val))
        except (ValueError, TypeError):
            return min_val
    
    # Sanitize all travel parameters
    destination = sanitize_input(travel_params.get('destination', ''), 50)
    days = validate_number(travel_params.get('days', '3'), 1, 30)
    people = validate_number(travel_params.get('people', '1'), 1, 100)
    accommodation = sanitize_input(travel_params.get('accommodation', 'mid-range'), 30)
    activities = sanitize_input(travel_params.get('activities', 'sightseeing'), 100)
    interests = sanitize_input(travel_params.get('interests', 'culture, food'), 100)
    pace = sanitize_input(travel_params.get('pace', 'balanced'), 30)
    trip_style = sanitize_input(travel_params.get('trip_style', 'first-time highlights'), 60)
    dietary = sanitize_input(travel_params.get('dietary', 'no preference'), 60)
    accessibility = sanitize_input(travel_params.get('accessibility', 'none'), 60)
    
    budget_raw = sanitize_input(travel_params.get('budget', 'medium'), 20)
    budget_amount = sanitize_input(travel_params.get('budget_amount', ''), 20)
    currency = sanitize_input(travel_params.get('currency', 'INR'), 10)
    
    # Formulate a descriptive budget label for storage
    if budget_amount:
        budget = f"{budget_raw.capitalize()} ({currency} {budget_amount})"
    else:
        budget = budget_raw.capitalize()
        
    travel_params['budget'] = budget
    travel_params['days'] = days
    travel_params['people'] = people
    
    if not destination:
        html_fallback = format_markdown_content(fallback_content["content"])
        return {
            "content": html_fallback,
            "sources": fallback_content["sources"],
            "plan_id": None
        }
    
    # Search for additional information using Tavily
    search_results = search_travel_info(
        f"travel guide for {destination}", 
        destination
    )
    
    # Extract useful information from search results
    search_info = ""
    sources = []
    
    if search_results:
        for i, result in enumerate(search_results[:5]):  # Limit to 5 results
            search_info += f"\nSource {i+1}: {sanitize_input(result.get('title', ''), 100)}\n"
            search_info += f"URL: {sanitize_input(result.get('url', ''), 200)}\n"
            text = result.get('content') or result.get('raw_content', '')
            search_info += f"Content: {sanitize_input(text, 300)}\n\n"
            
            sources.append({
                "name": result.get('title', 'Unknown'),
                "url": result.get('url', '')
            })
            
    # Construct budget requirements text
    budget_limit_prompt = ""
    if budget_amount:
        budget_limit_prompt = f"Make sure the total cost of all recommended items (accommodation, meals, transport, activities) fits strictly within a budget of {currency} {budget_amount}."
    
    # Build enhanced prompt for Gemini with sanitized parameters
    prompt = f"""Create a detailed {days}-day travel itinerary for {destination} in markdown format.

# {destination} - {days} Day Travel Plan

## Trip Overview
- Destination: {destination}
- Duration: {days} days
- Travelers: {people} people
- Budget: {budget}
- Accommodation: {accommodation}
- Activities: {activities}
- Interests: {interests}
- Travel pace: {pace}
- Trip style: {trip_style}
- Dietary needs: {dietary}
- Accessibility needs: {accessibility}

## Day-by-Day Itinerary

IMPORTANT: Create a detailed itinerary for EACH of the {days} days. For each day include:

- Use {currency} for all cost estimates and display the currency symbol correctly. {budget_limit_prompt}

### Day 1: [Theme/Focus]
**Morning (8:00 AM - 12:00 PM)**
- Activity 1: [Specific location/attraction]
  * Details and tips
  * Estimated time: X hours
  * Cost: {currency} XX
- Activity 2: [Another location]
  * Details and tips

**Afternoon (12:00 PM - 6:00 PM)**
- Lunch: [Restaurant recommendation]
- Activity 3: [Specific location]
  * Details and tips
- Activity 4: [Another location]

**Evening (6:00 PM - 10:00 PM)**
- Dinner: [Restaurant recommendation]
- Evening activity: [Specific location or experience]

[REPEAT THIS FORMAT FOR ALL {days} DAYS]

## Accommodation Recommendations
- Option 1: [Hotel/Airbnb name]
  * Location and why it's good
  * Price range: {currency} XX-{currency} XX per night
- Option 2: [Alternative]
- Option 3: [Budget option]

## Dining Guide
- Must-try dishes in {destination}
- Recommended restaurants:
  * Budget: [Name] - [Specialty]
  * Mid-range: [Name] - [Specialty]
  * Fine dining: [Name] - [Specialty]

## Transportation
- Getting to {destination}
- Getting around the city
- Estimated costs

## Budget Breakdown
- Accommodation: {currency} XX per night x {days} nights
- Meals: {currency} XX per day x {days} days
- Activities & Attractions: {currency} XX total
- Transportation: {currency} XX total
- **Total Estimated Cost: {currency} XXX - {currency} XXX**

## Local Tips & Essentials
- Best time to visit
- Local customs and etiquette
- Safety tips
- Useful phrases
- Emergency contacts

Additional context from research:
{search_info}

CRITICAL: You MUST create a complete day-by-day itinerary for all {days} days with specific activities, timings, and locations for morning, afternoon, and evening.

YOU MUST RETURN THE RESPONSE AS A JSON OBJECT WITH THE FOLLOWING SCHEMA:
{{
  "itinerary_markdown": "The complete travel plan in markdown format, matching the exact headers, day structure, overview, accommodation, dining, transportation, budget, and local tips sections specified above.",
  "days": [
    {{
      "day": 1,
      "stops": [
        {{
          "name": "Specific attraction name, restaurant name, or hotel name",
          "address": "Brief address or landmark location, e.g. Eiffel Tower, Paris, France",
          "lat": 48.8584,
          "lng": 2.2945,
          "time": "e.g. 08:00 AM",
          "description": "Short summary of the activity",
          "transport_to_next": "WALKING"
        }},
        ...
      ]
    }},
    ...
  ]
}}

Ensure that 'lat' and 'lng' are real numeric coordinates representing the exact location of the stop. The order of 'stops' must match the timeline of the day's itinerary. Set 'transport_to_next' to either 'WALKING', 'DRIVING', or 'CYCLING' to specify how to travel to the next stop.
"""
    
    try:
        if client is None:
            raise RuntimeError("GEMINI_API_KEY is missing. Set it in your environment before generating a plan.")

        # Request content with JSON configuration
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=DEFAULT_TEMPERATURE,
                max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                response_mime_type="application/json"
            )
        )
        raw_text = response.text
        
        # Parse JSON output
        try:
            cleaned_text = raw_text.strip()
            # Remove markdown code fences if present in the response
            code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', cleaned_text, re.DOTALL)
            if code_block_match:
                cleaned_text = code_block_match.group(1).strip()
            response_json = json.loads(cleaned_text)
            itinerary_markdown = response_json.get('itinerary_markdown', '')
            days_data = response_json.get('days', [])
            if not itinerary_markdown:
                itinerary_markdown = itinerary_json_to_markdown(
                    response_json, destination, days
                )
        except Exception as json_err:
            print(f"[DEBUG] JSON parsing failed: {json_err}")
            # Fallback if AI didn't output JSON
            itinerary_markdown = raw_text
            days_data = []

        # Add days_data to sources list as a metadata item
        sources.append({
            "type": "days_data",
            "data": days_data
        })
        
        # Save the plan to Supabase
        saved_plan = save_travel_plan(travel_params, itinerary_markdown, sources)
        
        # Convert markdown to HTML using the markdown library
        html_content = format_markdown_content(itinerary_markdown)
        
        return {
            "content": html_content,
            "sources": sources,
            "plan_id": saved_plan['id'] if saved_plan else None
        }
    except Exception as e:
        print(f"[DEBUG] Gemini API Error: {e}")
        print(f"[DEBUG] Error type: {type(e).__name__}")
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        print(f"[DEBUG] Returning fallback content (NO ITINERARY)")
        html_fallback = format_markdown_content(fallback_content["content"])
        return {
            "content": html_fallback,
            "sources": fallback_content["sources"],
            "plan_id": None
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/planner')
def planner():
    """New route for the dedicated planner page"""
    return render_template('planner.html')

@app.route('/generate_plan', methods=['GET', 'POST'])
def generate_plan():
    if request.method == 'GET':
        # Handle viewing existing plan
        plan_id = request.args.get('plan_id')
        if plan_id:
            plan_data = get_travel_plan(plan_id)
            if plan_data:
                # Convert stored content to HTML
                html_content = format_markdown_content(plan_data['content'])
                # Format the date using the new helper function
                formatted_date = format_date(plan_data.get('created_at'))
                
                return render_template('plan.html',
                                    plan=Markup(html_content),
                                    sources=plan_data.get('sources', []),
                                    params={
                                        'destination': plan_data['destination'],
                                        'days': plan_data['days'],
                                        'people': plan_data['people'],
                                        'accommodation': plan_data['accommodation'],
                                        'activities': plan_data['activities'],
                                        'interests': plan_data['interests'],
                                        'budget': plan_data['budget'],
                                        'pace': 'balanced',
                                        'trip_style': 'first-time highlights',
                                        'dietary': 'no preference',
                                        'accessibility': 'none'
                                    },
                                    plan_id=plan_id,
                                    generated_date=formatted_date)
            return redirect(url_for('planner'))

    # Store form data in session for plan regeneration if needed
    for key in request.form:
        session[key] = request.form.get(key)
    
    travel_params = {
        'destination': request.form.get('destination', ''),
        'days': request.form.get('days', '3'),
        'people': request.form.get('people', '1'),
        'accommodation': request.form.get('accommodation', 'mid-range'),
        'activities': request.form.get('activities', 'sightseeing'),
        'interests': request.form.get('interests', 'culture, food'),
        'budget': request.form.get('budget', 'medium'),
        'budget_amount': request.form.get('budget_amount', ''),
        'currency': request.form.get('currency', 'INR'),
        'pace': request.form.get('pace', 'balanced'),
        'trip_style': request.form.get('trip_style', 'first-time highlights'),
        'dietary': request.form.get('dietary', 'no preference'),
        'accessibility': request.form.get('accessibility', 'none')
    }
    
    # Validate inputs
    if not travel_params['destination']:
        return render_template('planner.html', error="Please provide a destination")
    
    # Show loading page while generating
    if request.form.get('ajax') == 'true':
        return jsonify({"status": "processing"})
    
    # Generate the travel plan
    result = generate_travel_plan(travel_params)
    
    return render_template('plan.html', 
                          plan=result["content"], 
                          sources=result.get("sources", []),
                          params=travel_params,
                          plan_id=result.get("plan_id"),
                          generated_date=datetime.now().strftime("%B %d, %Y"))

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/regenerate', methods=['POST'])
def regenerate_plan():
    # Retrieve stored parameters from session
    travel_params = {
        'destination': session.get('destination', ''),
        'days': session.get('days', '3'),
        'people': session.get('people', '1'),
        'accommodation': session.get('accommodation', 'mid-range'),
        'activities': session.get('activities', 'sightseeing'),
        'interests': session.get('interests', 'culture, food'),
        'budget': session.get('budget', 'medium'),
        'budget_amount': session.get('budget_amount', ''),
        'currency': session.get('currency', 'INR'),
        'pace': session.get('pace', 'balanced'),
        'trip_style': session.get('trip_style', 'first-time highlights'),
        'dietary': session.get('dietary', 'no preference'),
        'accessibility': session.get('accessibility', 'none')
    }
    
    # Generate a new plan with the same parameters
    result = generate_travel_plan(travel_params)
    
    return render_template('plan.html', 
                          plan=Markup(result["content"]), 
                          sources=result.get("sources", []),
                          params=travel_params,
                          plan_id=result.get("plan_id"),
                          generated_date=datetime.now().strftime("%B %d, %Y"))

@app.route('/plans')
def list_plans():
    """Route to display all saved travel plans"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9  # Number of plans per page
        
        # Get total count
        count_result = supabase.table('travel_plans').select('id', count='exact').execute()
        total_plans = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        # Calculate pagination
        total_pages = max((total_plans + per_page - 1) // per_page, 1)  # At least 1 page
        offset = (page - 1) * per_page
        
        # Get paginated results
        result = supabase.table('travel_plans').select("*").order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
        plans = result.data if result.data else []
        
        # Convert string timestamps to datetime objects
        for plan in plans:
            if isinstance(plan['created_at'], str):
                plan['created_at'] = datetime.fromisoformat(plan['created_at'].replace('Z', '+00:00'))
        
        return render_template('plans.html',
                             plans=plans,
                             current_page=page,
                             total_pages=total_pages,
                             prev_page=page-1 if page > 1 else None,
                             next_page=page+1 if page < total_pages else None)
    except Exception as e:
        print(f"Error fetching travel plans: {e}")
        return render_template('plans.html',
                             plans=[],
                             current_page=1,
                             total_pages=1,
                             prev_page=None,
                             next_page=None,
                             error="Failed to fetch travel plans")

@app.route('/travel-guides')
def travel_guides():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 9  # Number of guides per page
        
        # Get total count
        count_result = supabase.table('travel_guides').select('id', count='exact').execute()
        total_guides = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        # Calculate pagination
        total_pages = max((total_guides + per_page - 1) // per_page, 1)  # At least 1 page
        offset = (page - 1) * per_page
        
        # Get paginated results
        result = supabase.table('travel_guides').select("*").order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
        guides = result.data if result.data else []

        # Get unique categories
        categories = set(guide['category'] for guide in guides)
        
        return render_template('travel_guides.html',
                             guides=guides,
                             categories=categories,
                             current_page=page,
                             total_pages=total_pages,
                             prev_page=page-1 if page > 1 else None,
                             next_page=page+1 if page < total_pages else None)
    except Exception as e:
        print(f"Error fetching travel guides: {e}")
        return render_template('travel_guides.html',
                             guides=[],
                             categories=set(),
                             current_page=1,
                             total_pages=1,
                             prev_page=None,
                             next_page=None,
                             error="Failed to fetch travel guides")

@app.route('/travel-guides/create', methods=['GET', 'POST'])
def create_guide():
    if request.method == 'POST':
        try:
            data = {
                'title': request.form['title'],
                'content': request.form['content'],
                'excerpt': request.form['excerpt'],
                'author': request.form.get('author', 'Anonymous'),
                'category': request.form['category'],
                'tags': request.form['tags'].split(',') if request.form['tags'] else [],
                'icon': request.form.get('icon', 'compass'),
                'default_bg_color': request.form.get('default_bg_color', '#4F46E5')
            }
            
            # Associate user_id if user is authenticated in the session
            if 'user' in session:
                data['user_id'] = session['user']['id']
                
            result = supabase.table('travel_guides').insert(data).execute()
            
            if result.data:
                flash('Guide published successfully!', 'success')
                return redirect(url_for('travel_guides'))
            flash('Failed to create guide', 'error')
            return render_template('create_guide.html', error="Failed to create guide")
        except Exception as e:
            print(f"Error creating travel guide: {e}")
            flash('An error occurred while creating the guide', 'error')
            return render_template('create_guide.html', error="An error occurred while creating the guide")
    
    return render_template('create_guide.html')

@app.route('/travel-guides/<guide_id>')
def view_guide(guide_id):
    try:
        result = supabase.table('travel_guides').select("*").eq('id', guide_id).single().execute()
        if result.data:
            return render_template('view_guide.html', guide=result.data)
        return redirect(url_for('travel_guides'))
    except Exception as e:
        print(f"Error fetching travel guide: {e}")
        return redirect(url_for('travel_guides'))

@app.route('/hotel-search', methods=['GET', 'POST'])
def hotel_search():
    if request.method == 'POST':
        try:
            location = request.form.get('location')
            guests = request.form.get('guests', '2')
            preferences = request.form.get('preferences', '')
            budget = request.form.get('budget', 'medium')

            # Validate required fields
            if not location:
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('hotel_search'))

            # Search for hotel information using Tavily
            tavily_query = f"best hotels in {location} for {guests} guests with {budget} budget"
            if preferences:
                tavily_query += f" with {preferences} preferences"
            
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": TAVILY_API_KEY,
                "query": tavily_query,
                "search_depth": "advanced",
                "include_domains": [
                    "booking.com", "hotels.com", "expedia.com", 
                    "tripadvisor.com", "kayak.com"
                ],
                "max_results": 5
            }
            
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            hotel_results = response.json()

            if not hotel_results.get('results'):
                raise Exception("No results found from Tavily API")

            # Prepare search details section
            search_details = f"""
            ## Search Details
            - **Location**: {location}
            - **Guests**: {guests}
            - **Budget Level**: {budget}"""

            if preferences:
                search_details += f"\n- **Preferences**: {preferences}"

            # Prepare external sources section
            external_sources = "\n## External Sources"
            for result in hotel_results.get('results', []):
                external_sources += f"\n- [{result.get('title')}]({result.get('url')})\n  {result.get('snippet')}"

            # Generate hotel recommendations using Gemini
            prompt = f"""
            Create a detailed hotel recommendation guide in markdown format for:
            Location: {location}
            Guests: {guests}
            Preferences: {preferences}
            Budget: {budget}

            Use this structure:

            # Hotel Recommendations for {location}

            ## Overview
            [Brief introduction about {location} and its hotel scene]

            ## Top Recommended Hotels

            ### 1. [Hotel Name]
            - **Price Range**: [Budget details]
            - **Location**: [Area description]
            - **Key Features**:
              * [Feature 1]
              * [Feature 2]
              * [Feature 3]
            - **Best For**: [Type of travelers]
            - **Pros**:
              * [Pro 1]
              * [Pro 2]
            - **Cons**:
              * [Con 1]
              * [Con 2]

            [Repeat format for 4 more hotels]

            ## Location Guide
            - **Best Areas to Stay**:
              * [Area 1]: [Description]
              * [Area 2]: [Description]
              * [Area 3]: [Description]

            ## Price Analysis
            - **Budget Options**: [Price range and what to expect]
            - **Mid-Range Options**: [Price range and what to expect]
            - **Luxury Options**: [Price range and what to expect]

            {search_details}

            {external_sources}

            Use the following search results to enhance recommendations:
            {json.dumps(hotel_results.get('results', []), indent=2)}
            """

            if client is None:
                raise RuntimeError("GEMINI_API_KEY is missing. Set it in your environment before searching hotels.")

            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=DEFAULT_TEMPERATURE,
                    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS,
                )
            )
            if not response or not response.text:
                raise Exception("No response from Gemini API")

            # Save the search to the database
            search_data = {
                'location': location,
                'guests': int(guests),
                'preferences': preferences,
                'budget': budget,
                'recommendations': response.text,
                'search_results': hotel_results.get('results', [])
            }
            
            # Associate user_id if user is authenticated in the session
            if 'user' in session:
                search_data['user_id'] = session['user']['id']
                
            result = supabase.table('hotel_searches').insert(search_data).execute()
            if not result.data:
                raise Exception("Failed to save search to database")

            # Redirect to the view page for the new search
            return redirect(url_for('view_hotel_search', search_id=result.data[0]['id']))

        except requests.exceptions.RequestException as e:
            print(f"Tavily API Error: {str(e)}")
            print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            flash('Error connecting to hotel search service. Please try again.', 'error')
        except Exception as e:
            print(f"Error in hotel search: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            flash('An error occurred while searching for hotels. Please try again.', 'error')
        
        return redirect(url_for('hotel_search'))

    return render_template('hotel_search.html')

@app.route('/hotel-searches')
def hotel_searches():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 6  # Number of searches per page
        
        # Get total count
        count_result = supabase.table('hotel_searches').select('id', count='exact').execute()
        total_searches = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        
        # Calculate pagination
        total_pages = max((total_searches + per_page - 1) // per_page, 1)
        offset = (page - 1) * per_page
        
        # Get paginated results
        result = supabase.table('hotel_searches').select("*").order('created_at', desc=True).range(offset, offset + per_page - 1).execute()
        searches = result.data if result.data else []
        
        # Convert string timestamps to datetime objects
        for search in searches:
            if isinstance(search['created_at'], str):
                search['created_at'] = datetime.fromisoformat(search['created_at'].replace('Z', '+00:00'))
        
        return render_template('hotel_searches.html',
                             searches=searches,
                             current_page=page,
                             total_pages=total_pages,
                             prev_page=page-1 if page > 1 else None,
                             next_page=page+1 if page < total_pages else None)
    except Exception as e:
        print(f"Error fetching hotel searches: {e}")
        return render_template('hotel_searches.html',
                             searches=[],
                             current_page=1,
                             total_pages=1,
                             prev_page=None,
                             next_page=None,
                             error="Failed to fetch hotel searches")

@app.route('/hotel-search/<search_id>')
def view_hotel_search(search_id):
    try:
        result = supabase.table('hotel_searches').select("*").eq('id', search_id).single().execute()
        if result.data:
            # Convert markdown to HTML if recommendations exist
            if result.data.get('recommendations'):
                recommendations = bleach.clean(markdown.markdown(result.data['recommendations'], extensions=MARKDOWN_EXTENSIONS), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
                result.data['recommendations'] = recommendations
            return render_template('view_hotel_search.html', search=result.data)
        return redirect(url_for('hotel_searches'))
    except Exception as e:
        print(f"Error fetching hotel search: {e}")
        return redirect(url_for('hotel_searches'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==========================================
# ADVANCED AUTHENTICATION & DASHBOARD ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            # Sign up the user in Supabase Auth
            res = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            # Attempt to sign in directly
            login_res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if login_res.user:
                session['user'] = {
                    'id': login_res.user.id,
                    'email': login_res.user.email
                }
                flash("Account created and logged in successfully!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Account created! Please log in.", "success")
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if res.user:
                session['user'] = {
                    'id': res.user.id,
                    'email': res.user.email
                }
                flash("Logged in successfully!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid login credentials.", "danger")
        except Exception as e:
            flash(f"Login failed: {str(e)}", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for('login'))
        
    user_id = session['user']['id']
    try:
        # Fetch user's travel plans
        plans_res = supabase.table('travel_plans').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        plans = plans_res.data if plans_res.data else []
        
        # Fetch user's hotel searches
        hotels_res = supabase.table('hotel_searches').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        hotels = hotels_res.data if hotels_res.data else []
        
        # Fetch user's travel guides
        guides_res = supabase.table('travel_guides').select("*").eq('user_id', user_id).order('created_at', desc=True).execute()
        guides = guides_res.data if guides_res.data else []
        
        return render_template('dashboard.html', plans=plans, hotels=hotels, guides=guides)
    except Exception as e:
        print(f"Error loading dashboard: {str(e)}")
        flash("An error occurred loading your dashboard.", "danger")
        return render_template('dashboard.html', plans=[], hotels=[], guides=[])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)