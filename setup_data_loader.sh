#!/bin/bash

# ViaMigo Data Loader - Quick Setup Script
# This script helps you set up OpenTripMap integration quickly

echo "🇮🇹 ViaMigo Data Loader - Quick Setup 🇮🇹"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env file..."
    touch .env
    echo "✅ .env file created"
fi

# Check DATABASE_URL
if grep -q "DATABASE_URL=" .env; then
    echo "✅ DATABASE_URL found in .env"
else
    echo "⚠️  DATABASE_URL not found in .env"
    echo ""
    echo "Please add your PostgreSQL connection string to .env:"
    echo "DATABASE_URL=postgresql://user:password@host:port/viamigo_db"
    echo ""
    read -p "Do you want to add it now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter DATABASE_URL: " db_url
        echo "DATABASE_URL=$db_url" >> .env
        echo "✅ DATABASE_URL added to .env"
    fi
fi

# Check OPENTRIPMAP_API_KEY
if grep -q "OPENTRIPMAP_API_KEY=" .env; then
    echo "✅ OPENTRIPMAP_API_KEY found in .env"
else
    echo "⚠️  OPENTRIPMAP_API_KEY not found in .env"
    echo ""
    echo "📝 To get a FREE OpenTripMap API key:"
    echo "1. Visit: https://opentripmap.io/"
    echo "2. Sign up (free account)"
    echo "3. Copy your API key from dashboard"
    echo ""
    read -p "Do you have an API key ready? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter OPENTRIPMAP_API_KEY: " api_key
        echo "OPENTRIPMAP_API_KEY=$api_key" >> .env
        echo "✅ OPENTRIPMAP_API_KEY added to .env"
    else
        echo "⏸️  Setup paused. Get your API key from https://opentripmap.io/ and run this script again"
        exit 0
    fi
fi

echo ""
echo "🔍 Checking dependencies..."

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 installed"
else
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 installed"
else
    echo "❌ pip3 not found. Please install pip"
    exit 1
fi

# Check if sentence-transformers is installed
if python3 -c "import sentence_transformers" &> /dev/null; then
    echo "✅ sentence-transformers installed"
else
    echo "⚠️  sentence-transformers not installed"
    read -p "Install sentence-transformers now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install sentence-transformers
        echo "✅ sentence-transformers installed"
    else
        echo "⏸️  Please install manually: pip3 install sentence-transformers"
    fi
fi

# Check if chromadb is installed
if python3 -c "import chromadb" &> /dev/null; then
    echo "✅ chromadb installed"
else
    echo "⚠️  chromadb not installed"
    echo "Installing chromadb..."
    pip3 install chromadb
    echo "✅ chromadb installed"
fi

# Check if psycopg2 is installed
if python3 -c "import psycopg2" &> /dev/null; then
    echo "✅ psycopg2 installed"
else
    echo "⚠️  psycopg2 not installed"
    echo "Installing psycopg2-binary..."
    pip3 install psycopg2-binary
    echo "✅ psycopg2-binary installed"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📚 Next Steps:"
echo ""
echo "1️⃣  Review the guide:"
echo "    cat VIAMIGO_DATA_LOADER_GUIDE.md"
echo ""
echo "2️⃣  Load data for a single city (test):"
echo "    python3 -c \"from Viamigo_Data_Loader_Fixed import ViaMigoDataLoader; loader = ViaMigoDataLoader(); loader.load_city_data('Bergamo', 'it', radius=3000, limit=20); loader.close()\""
echo ""
echo "3️⃣  Load all Italian cities (full setup):"
echo "    python3 Viamigo_Data_Loader_Fixed.py"
echo ""
echo "4️⃣  Verify data loaded:"
echo "    python3 -c \"from simple_rag_helper import get_city_context; print(get_city_context('Bergamo', limit=5))\""
echo ""
echo "📊 Cost Comparison:"
echo "    cat DATA_SOURCES_COMPARISON.md"
echo ""
echo "🎉 Happy data loading!"
