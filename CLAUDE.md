# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an LLM-powered document assistance application for university students and researchers. The system helps users create documents (ES, research materials, reports) through a chat-based interface with project management capabilities.

## Tech Stack

- **Frontend**: TypeScript + React/Next.js + shadcn/ui
- **Backend**: Python + FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Authentication**: JWT-based authentication
- **LLM Integration**: OpenAI/Claude/Gemini (switchable)
- **External Integration**: Model Context Protocol (MCP) support via LangChain

## Architecture

### Database Schema
- `users`: JWT authentication with email/password
- `projects`: User-owned document projects
- `chat_logs`: Conversation history per project
- `llm_settings`: User-specific LLM provider configurations and API keys

### Key Components
- JWT authentication system for secure user sessions
- Project-based document organization
- Multi-provider LLM integration (OpenAI/Claude/Gemini)
- MCP tool integration using LangChain adapters
- Chat interface with conversation history

### MCP Tool Integration
- Tools defined with `spec + func` pattern
- Converted using `langchain.tools.mcp.convert_to_mcp_tool()`
- Executed via `AgentType.OPENAI_FUNCTIONS`
- JSON Schema compliant tool specifications
- Dynamic tool registration from database/config

## Development Commands

### Recommended Setup (Backend: Docker, Frontend: Local)
```bash
# 1. Start backend services with Docker
./scripts/start-backend.sh

# 2. Start frontend locally (in another terminal)
./scripts/start-frontend.sh

# Stop backend services
./scripts/stop-backend.sh
```

### Alternative: Full Docker Setup
```bash
# Everything in Docker
./scripts/setup.sh
```

### Manual Commands

#### Backend (Docker)
```bash
docker compose -f docker-compose.backend.yml up --build -d
docker compose -f docker-compose.backend.yml exec backend alembic upgrade head
```

#### Frontend (Local)
```bash
cd frontend
npm install
npm run dev  # Start development server
npm run build  # Build for production
```

### Database Operations
```bash
cd backend
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head  # Apply migrations
alembic downgrade -1  # Rollback one migration
```

## Security Considerations
- User API keys are stored per provider in `llm_settings`
- JWT tokens handle user authentication
- Database foreign key relationships enforce data isolation per user