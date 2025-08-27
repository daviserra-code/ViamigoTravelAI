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
- **January 26, 2025**: Added dedicated `/health` endpoint for deployment monitoring
- **January 26, 2025**: Enhanced root endpoint with fallback responses for deployment reliability
- **January 26, 2025**: Updated workflow configuration with explicit main.py entry point
- **January 26, 2025**: Created dedicated `run.py` entry point for deployment with proper environment handling
- **January 26, 2025**: Fixed workflow configuration to use `python run.py` command for reliable deployment startup
- **January 26, 2025**: Added support for HEAD requests on health endpoints for deployment monitoring
- **January 26, 2025**: Fixed static map issue - map now properly resets and updates for new itineraries
- **January 26, 2025**: Improved image search algorithm with multiple fallback queries and better matching
- **January 26, 2025**: Enhanced image database with more locations and smarter matching algorithms