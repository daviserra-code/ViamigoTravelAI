# Viamigo - AI-Powered Travel Organizer

## Overview
Viamigo is an AI-powered travel recommendation system designed to provide personalized travel suggestions using Retrieval Augmented Generation (RAG). It combines vector-based document retrieval with Large Language Models to deliver contextually relevant recommendations based on user queries. The system is built to offer a seamless travel planning experience, integrating diverse data sources to minimize AI hallucinations and provide accurate, actionable itineraries.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Hybrid architecture utilizing FastAPI for AI/API endpoints and Flask for the web interface and authentication.
- **Architecture Pattern**: Service-oriented architecture ensuring clear separation of concerns.
- **Application Lifecycle**: Managed startup/shutdown processes with proper resource initialization and cleanup.
- **Routing**: Modular organization of routes, with distinct modules for travel recommendations and health checks.

### RAG (Retrieval Augmented Generation) Pipeline
- **Core Design**: A three-stage pipeline integrating document retrieval with LLM-based generation.
- **Query Enhancement**: Uses LLM for refining user queries to improve document matching.
- **Document Retrieval**: Employs vector similarity search via ChromaDB with configurable thresholds.
- **Context Integration**: Retrieved documents form the context for LLM recommendation generation.
- **Post-processing**: Recommendations are ranked and filtered based on relevance scores.
- **Geographic Validation**: Includes an anti-hallucination system that verifies GPS coordinates, especially for Italian cities, and automatically corrects inaccurate AI-generated coordinates.
- **Scalable Universal System**: Designed to support any Italian/European city with a multi-tiered approach: local database, dynamic cache for API-discovered cities, intelligent geographic fallback, and automated coverage for medium/small cities.
- **Dynamic Worldwide System**: Hybrid architecture combining a local database for Italian cities with a dynamic API system for global destinations, utilizing OpenStreetMap, Nominatim, and AI for authentic worldwide travel information.

### Vector Database Layer
- **Storage**: ChromaDB is used for persistent vector storage, with configurable data directory.
- **Collections**: A single collection approach for travel data with comprehensive metadata support.
- **Initialization**: Automatic collection creation, including initial seeding with travel data.
- **Operations**: Supports document addition, similarity search, and collection statistics.

### LLM Integration
- **Multi-provider Support**: Configurable to support both OpenAI and Google Gemini models.
- **Primary Provider**: OpenAI, with GPT-5 as the default model.
- **Fallback Strategy**: Implements graceful handling for unavailable LLM services.
- **Context Management**: Dynamic preparation of context from retrieved documents for LLM processing.

### Data Models
- **Request/Response**: Utilizes Pydantic models for type safety and validation.
- **Travel Queries**: Structured to support detailed queries including destinations, budgets, dates, and preferences.
- **Recommendations**: Standardized format providing confidence scores and detailed information.
- **Enumerations**: Type-safe enumerations for travel categories and preferences.

### Configuration Management
- **Settings**: Centralized configuration managed via Pydantic Settings.
- **Environment Variables**: Supports `.env` files and environment-based configuration.
- **Defaults**: Provides sensible default values for all configurable parameters.
- **Validation**: Includes type checking and validation for all configuration values.

### Error Handling and Monitoring
- **Logging**: Structured logging with configurable levels and multiple handlers.
- **Health Checks**: Comprehensive monitoring of service health, including ChromaDB and LLM status.
- **Exception Management**: Proper HTTP status codes and error responses for exceptions.
- **Service Dependencies**: Dependency injection pattern is used for service management.
- **Circuit Breaker Pattern**: Implemented automatic circuit breaking for external API failures with configurable thresholds.
- **API Response Caching**: Time-based caching system for expensive API calls (OpenAI, ScrapingDog, Nominatim) to reduce costs.
- **Resilient API Calls**: Automatic retry logic with exponential backoff for temporary failures.

### UI/UX and Feature Specifications
- **Unified Mobile Design**: All profile pages use a consistent mobile phone mockup design.
- **Modern Login UI**: Integrated Gemini-designed login page with Viamigo branding and mobile-first design.
- **Dashboard Navigation**: Added a dashboard button in the mobile app header for direct access.
- **Intelligent Travel Companion**: Features include "Piano B Dinamico" for unforeseen events, "Scoperte Intelligenti" for contextual suggestions, and "Diario di Viaggio AI" for behavioral analysis.

## External Dependencies

### AI/ML Services
- **OpenAI API**: Primary Large Language Model provider for generating travel recommendations (using GPT-4-turbo).
- **Google Gemini**: An alternative LLM provider with fallback support.
- **ChromaDB**: Utilized as the vector database for document storage and similarity search.

### Core Framework Dependencies
- **FastAPI**: The web framework, providing automatic API documentation.
- **Uvicorn**: The ASGI server used for production deployment.
- **Pydantic**: Employed for data validation and managing application settings.
- **Python Asyncio**: Provides support for asynchronous programming within the application.

### APIs and Integrations
- **OpenRouteService API**: Integrated for authentic pedestrian routes and multi-modal transport support.
- **OpenStreetMap & Nominatim**: Used for dynamic worldwide geocoding and coordinate validation.
- **CORS Middleware**: Supports cross-origin requests for web clients.
- **PostgreSQL**: Backend database for user profile management.