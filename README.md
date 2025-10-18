# Viamigo Travel AI 🇮🇹✈️

An AI-powered travel companion that helps you plan personalized itineraries for Italian cities and beyond.

## Features

- 🤖 **AI-Powered Planning**: Generate intelligent, personalized travel itineraries
- 🗺️ **Interactive Maps**: Visualize your route with interactive mapping
- 🎯 **Smart Recommendations**: Get personalized place suggestions based on your preferences
- 🌐 **Multi-Language Support**: Available in multiple languages
- 📱 **Real-Time Updates**: Weather, crowds, and event monitoring
- 💾 **User Profiles**: Save preferences and trip history

## Quick Start

### For Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/daviserra-code/ViamigoTravelAI.git
   cd ViamigoTravelAI
   ```

2. **Set up environment**:
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**:
   ```bash
   python3 run.py
   ```

5. **Access the app**: Open http://localhost:5000 in your browser

For detailed setup instructions, including database configuration and API key setup, see **[SETUP.md](SETUP.md)**.

**Setup Checklist**: Use [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) to verify your installation is complete.

### For Deployment (Replit/Production)

The project includes deployment configurations:
- Copy `.env.example` to `.env` and set variables
- Run `./start.sh` to start the production server

## Documentation

- 📖 **[SETUP.md](SETUP.md)** - Complete local development setup guide
- 📋 **[Instructions.md](Instructions.md)** - Detailed implementation plan and architecture
- 🗃️ **[VIAMIGO_DATA_LOADER_GUIDE.md](VIAMIGO_DATA_LOADER_GUIDE.md)** - Data loading and caching
- 📊 **[DATA_SOURCES_COMPARISON.md](DATA_SOURCES_COMPARISON.md)** - API comparison and costs

## Technology Stack

- **Backend**: Python, Flask
- **AI**: OpenAI GPT
- **Database**: PostgreSQL / SQLite
- **Vector DB**: ChromaDB
- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Maps**: Leaflet.js
- **APIs**: Geoapify, Apify, OpenTripMap

## Project Structure

```
ViamigoTravelAI/
├── app/                    # Application modules
├── static/                 # Static files (CSS, JS, images)
├── run.py                  # Application entry point
├── flask_app.py           # Flask setup
├── routes.py              # Main routes
├── ai_companion_routes.py # AI features
├── requirements.txt       # Python dependencies
└── SETUP.md              # Setup instructions
```

## Requirements

- Python 3.8+
- Node.js (for frontend dependencies)
- PostgreSQL (optional, SQLite fallback available)

## Contributing

Contributions welcome! Please:
1. Read [SETUP.md](SETUP.md) for local development setup
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add license information]

## Support

For issues or questions:
- Check [SETUP.md](SETUP.md) for troubleshooting
- Open an issue on GitHub

---

**Made with ❤️ for travelers**

