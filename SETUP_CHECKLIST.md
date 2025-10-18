# Setup Verification Checklist

Use this checklist to verify your Viamigo Travel AI local setup is complete and working.

## ✅ Prerequisites Check

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] pip installed (`pip3 --version`)
- [ ] Node.js installed (`node --version`)
- [ ] npm installed (`npm --version`)
- [ ] Git installed (`git --version`)

## ✅ Repository Setup

- [ ] Repository cloned to local machine
- [ ] Can navigate to project directory
- [ ] `.git` directory exists (not a zip download)

## ✅ Environment Setup

- [ ] Virtual environment created (`venv` directory exists)
- [ ] Virtual environment activated (prompt shows `(venv)`)
- [ ] Python dependencies installed (`pip list` shows Flask, openai, etc.)
- [ ] Node dependencies installed (`node_modules` directory exists)

## ✅ Configuration

- [ ] `.env` file created (copied from `.env.example`)
- [ ] `OPENAI_API_KEY` set in `.env` (get from [OpenAI](https://platform.openai.com))
- [ ] `APIFY_API_TOKEN` set in `.env` (optional but recommended)
- [ ] `GEOAPIFY_KEY` set in `.env` (optional but recommended)
- [ ] `DATABASE_URL` set if using PostgreSQL (optional, SQLite fallback available)
- [ ] `PORT` set (default: 5000)

## ✅ Database Setup (Optional)

If using PostgreSQL:
- [ ] PostgreSQL installed and running
- [ ] Database created
- [ ] Connection string added to `.env`
- [ ] Tables created successfully

If using SQLite (fallback):
- [ ] App runs without DATABASE_URL
- [ ] SQLite file created automatically

## ✅ Application Start

- [ ] Application starts without errors: `python3 run.py`
- [ ] No missing module errors
- [ ] No configuration errors
- [ ] Server listens on expected port
- [ ] Console shows: `Running on http://...`

## ✅ Basic Functionality

- [ ] Can access app in browser (http://localhost:5000)
- [ ] Home page loads
- [ ] No 500 errors in console
- [ ] Static files load (CSS, JS)

## ✅ Optional Features

- [ ] ChromaDB working (vector database for AI features)
- [ ] Sample data loaded (`chromadb_data` directory exists)
- [ ] Authentication working (can create/login users)
- [ ] API integrations working (with valid API keys)

## 🔧 Quick Tests

Run these commands to verify specific components:

### Test Database Connection
```bash
python3 -c "from flask_app import create_tables; create_tables(); print('✅ Database OK')"
```

### Test ChromaDB
```bash
python3 -c "import chromadb; print('✅ ChromaDB OK')"
```

### Test OpenAI Integration (requires API key)
```bash
python3 -c "from openai import OpenAI; import os; client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print('✅ OpenAI OK')"
```

### Test Flask Routes
```bash
# Start the server in one terminal
python3 run.py

# In another terminal, test the endpoint
curl http://localhost:5000/
```

## 🐛 Troubleshooting

If any check fails, see [SETUP.md](SETUP.md) Troubleshooting section for common issues:

- Port already in use → Change PORT in `.env`
- Module not found → Reinstall dependencies: `pip install -r requirements.txt`
- Database errors → Check DATABASE_URL or use SQLite fallback
- API errors → Verify API keys in `.env`

## 📋 Success Criteria

Your setup is complete when:

1. ✅ All prerequisite checks pass
2. ✅ Application starts without errors
3. ✅ You can access the app in browser
4. ✅ At least basic functionality works

## 🚀 Next Steps

Once verified, you can:

1. **Load sample data**: Run `./setup_data_loader.sh`
2. **Create an account**: Visit `/auth/register` 
3. **Try the AI features**: Create your first itinerary
4. **Read the documentation**: Check [Instructions.md](Instructions.md)

## 💡 Tips

- Keep your virtual environment activated while working
- Check console logs for errors
- Use browser DevTools to debug frontend issues
- Test API keys separately before running the full app

---

**Last Updated**: October 2025
