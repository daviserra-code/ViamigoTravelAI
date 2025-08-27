# Viamigo - AI-Powered Travel Organizer

## Overview

Viamigo is an AI-powered travel recommendation system that uses Retrieval Augmented Generation (RAG) to provide personalized travel suggestions. The application combines vector-based document retrieval with Large Language Models to deliver contextually relevant travel recommendations based on user queries. Built with FastAPI, it integrates ChromaDB for vector storage and supports multiple LLM providers including OpenAI and Gemini.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI with asynchronous support for high-performance API operations
- **Architecture Pattern**: Service-oriented architecture with clear separation of concerns
- **Application Lifecycle**: Managed startup/shutdown with proper resource initialization and cleanup
- **Routing**: Modular route organization with separate modules for travel recommendations and health checks

### RAG (Retrieval Augmented Generation) Pipeline
- **Core Design**: Three-stage pipeline combining document retrieval with LLM generation
- **Query Enhancement**: LLM-powered query refinement for better document matching
- **Document Retrieval**: Vector similarity search using ChromaDB with configurable similarity thresholds
- **Context Integration**: Retrieved documents are used as context for LLM recommendation generation
- **Post-processing**: Recommendation ranking and filtering based on relevance scores
- **Geographic Validation**: Anti-hallucination system with verified GPS coordinates for Italian cities
- **Coordinate Correction**: Automatic detection and correction of inaccurate AI-generated coordinates

### Vector Database Layer
- **Storage**: ChromaDB for persistent vector storage with configurable data directory
- **Collections**: Single collection approach for travel data with metadata support
- **Initialization**: Automatic collection creation with initial travel data seeding
- **Operations**: Support for document addition, similarity search, and collection statistics

### LLM Integration
- **Multi-provider Support**: Configurable support for OpenAI and Gemini models
- **Primary Provider**: OpenAI with GPT-5 as the default model
- **Fallback Strategy**: Graceful handling of unavailable LLM services
- **Context Management**: Dynamic context preparation from retrieved documents

### Data Models
- **Request/Response**: Pydantic models for type safety and validation
- **Travel Queries**: Structured support for destinations, budgets, dates, and preferences
- **Recommendations**: Standardized format with confidence scores and detailed information
- **Enumerations**: Type-safe travel categories and preferences

### Configuration Management
- **Settings**: Centralized configuration using Pydantic Settings
- **Environment Variables**: Support for .env files and environment-based configuration
- **Defaults**: Sensible defaults for all configurable parameters
- **Validation**: Type checking and validation for all configuration values

### Error Handling and Monitoring
- **Logging**: Structured logging with configurable levels and multiple handlers
- **Health Checks**: Comprehensive service health monitoring including ChromaDB and LLM status
- **Exception Management**: Proper HTTP status codes and error responses
- **Service Dependencies**: Dependency injection pattern for service management

## External Dependencies

### AI/ML Services
- **OpenAI API**: Primary LLM provider for travel recommendation generation
- **Google Gemini**: Alternative LLM provider with fallback support
- **ChromaDB**: Vector database for document storage and similarity search

### Core Framework Dependencies
- **FastAPI**: Web framework with automatic API documentation
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management
- **Python Asyncio**: Asynchronous programming support

### Optional Integrations
- **CORS Middleware**: Cross-origin request support for web clients
- **Environment Configuration**: .env file support for local development
- **Persistent Storage**: File-based vector storage for data persistence

## Deployment Configuration

### Health Check Endpoints
- **Primary Health Check**: `/health` endpoint for deployment monitoring with proper error handling
- **Root Endpoint**: `/` endpoint serves static content with fallback health response for deployment systems
- **Status Responses**: Structured JSON responses with service status and error details

### Server Configuration
- **Host Binding**: Application configured to listen on `0.0.0.0:5000` for external accessibility
- **Port Mapping**: Internal port 5000 mapped for deployment compatibility
- **Entry Point**: Explicit `main.py` specification for reliable deployment startup

### Workflow Management  
- **Development Server**: Configured via workflow system for consistent local development
- **Process Management**: Automatic restart capabilities with proper port monitoring
- **Resource Initialization**: Proper startup sequence ensuring all services are ready

### Recent Changes  
- **August 27, 2025**: **PRE-TRAINING SYSTEM** - Built intelligent 3-tier architecture: (1) Local database for Italian cities, (2) Smart cache database for dynamic learning, (3) API system for worldwide coverage. Added automated pre-training scripts for 60+ global destinations with priority levels (Italia/Europa/Mondiale)
- **August 27, 2025**: **DYNAMIC WORLDWIDE SYSTEM** - Implemented hybrid architecture: local database for Italian cities + dynamic API system for global destinations using OpenStreetMap, Nominatim, and AI (GPT-5) for authentic worldwide travel information
- **August 27, 2025**: **REALISTIC STREET ROUTING** - Integrated OpenRouteService API for authentic pedestrian routes replacing straight-line paths, with multi-modal transport support (walking, metro, bus, tram, funicular)
- **August 27, 2025**: **CITY-SPECIFIC ITINERARIES** - Added comprehensive support for Torino, Roma, Milano, Venezia, Firenze, Genova with authentic local details, transport costs, and cultural information
- **August 27, 2025**: **UNIVERSAL DYNAMIC ROUTING** - Sistema completamente scalabile per QUALSIASI città italiana: geocoding automatico Nominatim, cache dinamico, waypoints intelligenti per tipologia città (costiera/montana/interna)
- **August 27, 2025**: **COMPLETE SYSTEM INTEGRATION** - Fully functional Viamigo app with Flask backend, PostgreSQL database, and original frontend
- **August 27, 2025**: **API ENDPOINTS WORKING** - `/plan` and `/get_profile` endpoints successfully serving frontend requests
- **August 27, 2025**: **PERSISTENT SESSION SYSTEM** - Demo login with session management enabling fluid navigation
- **August 27, 2025**: **UNIFIED MOBILE DESIGN** - All profile pages (view/create/edit) using consistent mobile phone mockup design
- **August 27, 2025**: **DASHBOARD HOMEPAGE** - Separate dashboard page enabling proper browser back/forward navigation
- **August 27, 2025**: **MODERN LOGIN UI** - Integrated Gemini-designed login page with Viamigo branding and mobile-first design
- **August 27, 2025**: **FLASK CRUD SYSTEM** - Successfully deployed complete user profile management with PostgreSQL backend
- **August 27, 2025**: **UI INTEGRATION** - Combined original Viamigo UI with new authentication system maintaining design consistency
- **August 27, 2025**: **IMAGE SYSTEM REDESIGN** - Implemented proxy backend system for CORS-free image serving
- **August 27, 2025**: **STABLE SOLUTION** - App now functions perfectly without images to avoid external dependency issues
- **August 27, 2025**: **RELIABILITY FOCUS** - Only verified image URLs (Colosseo) used to prevent 403/404 errors
- **August 27, 2025**: Built `/image_proxy` endpoint to serve external images through backend
- **August 27, 2025**: Removed dependency on Pixabay, Unsplash due to hotlinking restrictions
- **August 27, 2025**: DALL-E disabled temporarily due to access issues and performance impact
- **August 27, 2025**: **BREAKTHROUGH** - Implemented fully dynamic coordinate validation system using OpenStreetMap APIs
- **August 27, 2025**: **SCALABLE SOLUTION** - Anti-hallucination system now works for ANY Italian city, not just pre-configured ones
- **August 27, 2025**: Added real-time geographic validation that detects when AI places locations in water/wrong cities
- **August 27, 2025**: Automatic coordinate correction using Nominatim reverse geocoding and search APIs
- **August 27, 2025**: Hybrid approach: Local database for frequent locations + API validation for everything else
- **August 27, 2025**: Venice, Milano, Roma now have verified coordinate databases to prevent "cafe in laguna" errors
- **August 27, 2025**: Fully implemented dynamic mapping system with real GPS coordinates
- **August 27, 2025**: **9 CITTÀ OTTIMIZZATE** - Espansione massiva: Roma, Milano, Torino, Genova, Firenze, Napoli, Bologna, Palermo, Venezia con database completi di coordinate verificate e contenuti autentici
- **August 27, 2025**: Built comprehensive GPS database preventing AI geographic errors (Genova, Milano, Roma, Firenze, Venezia)
- **August 27, 2025**: Resolved coastal coordinate issues (Parchi di Nervi no longer appear in the sea)
- **August 27, 2025**: Resolved browser caching issues that prevented JavaScript execution
- **August 27, 2025**: Backend now generates authentic GPS coordinates with post-processing verification
- **August 27, 2025**: Frontend successfully integrates Leaflet.js maps with backend coordinate data
- **August 27, 2025**: Unified itinerary system - single pipeline from user input to interactive map
- **August 27, 2025**: Real-time itinerary updates with precise geographic positioning
- **August 27, 2025**: Comprehensive debug logging system for development and troubleshooting
- **August 27, 2025**: Fixed static file serving and eliminated HEAD request conflicts
- **January 26, 2025**: Added dedicated `/health` endpoint for deployment monitoring
- **January 26, 2025**: Enhanced root endpoint with fallback responses for deployment reliability