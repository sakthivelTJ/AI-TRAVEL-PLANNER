#!/bin/bash
# Quick Start Script for AI Travel Planner

echo "🌍 AI Travel Planner - Quick Start"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
. venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Check .env file
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found!"
    echo "Please create a .env file with your API keys:"
    echo ""
    echo "GEMINI_API_KEY=your_key_here"
    echo "TAVILY_API_KEY=your_key_here"
    echo "VITE_SUPABASE_ANON_KEY=your_key_here"
    echo "VITE_SUPABASE_URL=your_url_here"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting Flask application..."
echo "   Access the app at: http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Run the app
python app.py
