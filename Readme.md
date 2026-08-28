# 🌍 AI Travel Planner

An intelligent travel planning application that uses AI to generate personalized itineraries, search hotels, and create detailed travel guides.

Link : https://ai-travel-planner-v821.onrender.com

## 📋 Features

- **AI-Powered Itinerary Generation** - Get personalized travel plans powered by Google Gemini AI
- **Travel Guides** - Create and view comprehensive travel guides for destinations
- **Hotel Search** - Search and view hotel options for your travel dates
- **Multi-day Planning** - Plan trips spanning multiple days with detailed day-by-day itineraries
- **Database Storage** - Save your travel plans using Supabase PostgreSQL
- **Responsive UI** - Mobile-friendly web interface built with Flask and Bootstrap

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API Key
- Tavily Search API Key
- Supabase Account & Database URL

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/sakthivelTJ/AI-TRAVEL-PLANNER.git
cd AI-Travel-Planner
```

2. **Create a virtual environment**

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # macOS/Linux
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
   Create a `.env` file in the project root:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_OUTPUT_TOKENS=8000
```

5. **Run the application**

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
AI-Travel-Planner/
├── app.py                 # Main Flask application
├── config.py              # Configuration and environment variables
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── planner.html       # Travel planner page
│   ├── plans.html         # Saved plans list
│   ├── hotel_search.html  # Hotel search page
│   └── travel_guides.html # Travel guides page
├── static/
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── images/            # Images and assets
└── supabase/
    └── migrations/        # Database migrations
```

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **AI/ML**: Google Gemini API
- **Search**: Tavily Search API
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Authentication**: Supabase Auth (optional)

## 📝 Usage

### Creating a Travel Plan

1. Go to the Planner page
2. Enter your travel destination and dates
3. AI generates a personalized itinerary
4. Save your plan to the database

### Searching Hotels

1. Use the Hotel Search feature
2. Enter destination and check-in/out dates
3. View available hotels and book

### Creating Travel Guides

1. Create custom guides for destinations
2. Add detailed information and tips
3. Share with other users

## 🔐 Environment Variables

| Variable                    | Description                |
| --------------------------- | -------------------------- |
| `VITE_SUPABASE_URL`         | Your Supabase project URL  |
| `VITE_SUPABASE_ANON_KEY`    | Supabase anonymous key     |
| `GEMINI_API_KEY`            | Google Gemini API key      |
| `TAVILY_API_KEY`            | Tavily Search API key      |
| `DEFAULT_TEMPERATURE`       | AI model temperature (0-1) |
| `DEFAULT_MAX_OUTPUT_TOKENS` | Max tokens for AI response |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

For issues, questions, or suggestions:

- Open an issue on [GitHub Issues](https://github.com/sakthivelTJ/AI-TRAVEL-PLANNER/issues)
- Check existing documentation in the repository

## 🎯 Roadmap

- [ ] User authentication and profiles
- [ ] Social sharing features
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Advanced filtering for hotels
- [ ] Budget-based itinerary planning
- [ ] Real-time collaboration features

---

Made with ❤️ by Sakthivel
