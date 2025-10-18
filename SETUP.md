# Viamigo Travel AI - Local Setup Guide

This guide will help you set up the Viamigo Travel AI project on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **pip** (Python package manager, usually comes with Python)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **PostgreSQL** (optional, for production database) - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Node.js and npm** (for frontend dependencies) - [Download Node.js](https://nodejs.org/)

## Step 1: Clone the Repository

```bash
git clone https://github.com/daviserra-code/ViamigoTravelAI.git
cd ViamigoTravelAI
```

## Step 2: Set Up Python Virtual Environment

It's recommended to use a virtual environment to isolate project dependencies:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install all required Python packages including:
- Flask (web framework)
- OpenAI (AI integration)
- ChromaDB (vector database)
- SQLAlchemy (database ORM)
- And many more...

## Step 4: Install Node.js Dependencies

The project uses Tailwind CSS for styling:

```bash
npm install
```

## Step 5: Configure Environment Variables

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your API keys and configuration:

```env
# Server Configuration
PORT=3000
NODE_ENV=development
BASE_URL=http://localhost:3000

# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
GEOAPIFY_KEY=your_geoapify_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/viamigo_db

# Admin Secret (Change in production!)
ADMIN_SECRET=change-this-secret-key-in-production
```

### Getting API Keys

1. **OpenAI API Key**: 
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Navigate to API Keys section
   - Create a new secret key

2. **Apify API Token**:
   - Sign up at [Apify](https://apify.com/)
   - Get your API token from account settings

3. **Geoapify Key**:
   - Sign up at [Geoapify](https://www.geoapify.com/)
   - Get your API key from dashboard

4. **OpenTripMap API Key** (Optional, for enhanced place data):
   - Sign up at [OpenTripMap](https://opentripmap.io/)
   - Get your free API key

## Step 6: Set Up Database

### Option A: PostgreSQL (Recommended for Production)

1. Install PostgreSQL on your system
2. Create a new database:

```bash
createdb viamigo_db
```

3. Update the `DATABASE_URL` in your `.env` file with your PostgreSQL credentials

### Option B: SQLite (Quick Start for Development)

The application will automatically create a SQLite database if PostgreSQL is not configured.

## Step 7: Initialize the Database

The application will automatically create necessary tables on first run. However, you can explicitly initialize:

```bash
python3 -c "from flask_app import create_tables; create_tables()"
```

## Step 8: Load Initial Data (Optional)

### Quick Setup with OpenTripMap Integration

Run the automated setup script:

```bash
./setup_data_loader.sh
```

This script will:
- Check your environment configuration
- Verify dependencies
- Guide you through API key setup
- Help you load initial city data

### Manual Data Loading

Load data for specific Italian cities:

```bash
python3 Viamigo_Data_Loader_Fixed.py
```

Or load data for a single city:

```bash
python3 -c "from Viamigo_Data_Loader_Fixed import ViaMigoDataLoader; loader = ViaMigoDataLoader(); loader.load_city_data('Rome', 'it', radius=5000, limit=50); loader.close()"
```

## Step 9: Run the Application

### Development Mode

```bash
python3 run.py
```

The application will be available at `http://localhost:5000` (or the PORT specified in `.env`)

### Production Mode

```bash
./start.sh
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, change the `PORT` in your `.env` file:

```env
PORT=8000
```

### Database Connection Issues

If you encounter database connection errors:

1. Verify PostgreSQL is running:
   ```bash
   # On Linux/Mac:
   sudo systemctl status postgresql
   # On Mac with Homebrew:
   brew services list
   ```

2. Check your `DATABASE_URL` format:
   ```
   postgresql://username:password@localhost:5432/database_name
   ```

3. For SQLite (fallback), no additional configuration needed

### Missing Dependencies

If you get import errors, ensure all dependencies are installed:

```bash
pip install -r requirements.txt --upgrade
```

### ChromaDB Data Issues

If ChromaDB throws errors, you can reset the vector database:

```bash
rm -rf chromadb_data/
```

The application will recreate it on next run.

### API Rate Limits

Some free APIs have rate limits:
- OpenAI: Monitor your usage on the [OpenAI dashboard](https://platform.openai.com/usage)
- Geoapify: 3000 requests/day on free tier
- OpenTripMap: 1000 requests/day on free tier

## Project Structure

```
ViamigoTravelAI/
├── app/                    # Application modules
├── static/                 # Static files (CSS, JS, images)
├── chromadb_data/         # Vector database storage
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── run.py                 # Application entry point
├── flask_app.py          # Flask application setup
├── routes.py             # Main routes
├── ai_companion_routes.py # AI features routes
├── auth_routes.py        # Authentication routes
└── README.md             # Project overview
```

## Key Features

- **AI-Powered Itinerary Planning**: Generate personalized travel itineraries
- **Smart Place Recommendations**: AI suggests attractions based on preferences
- **Interactive Maps**: Visualize routes with Leaflet.js
- **Multi-Language Support**: Available in multiple languages
- **Real-Time Data**: Integration with multiple travel APIs
- **User Profiles**: Save preferences and trip history

## Development Tips

1. **Hot Reload**: Use Flask's debug mode for auto-reload:
   ```python
   # In run.py, set debug=True for development
   app.run(debug=True)
   ```

2. **Database Migrations**: After model changes, reinitialize:
   ```bash
   python3 -c "from flask_app import create_tables; create_tables()"
   ```

3. **Testing API Endpoints**: Use tools like:
   - [Postman](https://www.postman.com/)
   - [curl](https://curl.se/)
   - Browser DevTools

4. **Monitoring Logs**: Check console output for debugging information

## Additional Resources

- [Instructions.md](Instructions.md) - Detailed implementation plan and architecture
- [VIAMIGO_DATA_LOADER_GUIDE.md](VIAMIGO_DATA_LOADER_GUIDE.md) - Data loading guide
- [DATA_SOURCES_COMPARISON.md](DATA_SOURCES_COMPARISON.md) - API comparison
- [ADMIN_CACHE_GUIDE.md](ADMIN_CACHE_GUIDE.md) - Cache management

## Getting Help

If you encounter issues not covered in this guide:

1. Check existing documentation in the repository
2. Review the [Issues](https://github.com/daviserra-code/ViamigoTravelAI/issues) page
3. Create a new issue with:
   - Your environment details (OS, Python version)
   - Steps to reproduce the problem
   - Error messages or logs

## Contributing

Contributions are welcome! Please ensure your local setup is working before making changes.

## License

[Add license information here]

---

**Last Updated**: October 2025
**Maintainer**: Davis Serra
