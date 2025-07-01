# LLM Chat App Backend

Document assistance application backend using FastAPI with MCP (Model Context Protocol) integration.

## Architecture

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based user authentication
- **LLM Integration**: Multi-provider support (OpenAI, Claude, Gemini)
- **MCP Integration**: Official MCP client with LangChain adapter

## Key Files

### Core Application
- `main.py` - FastAPI application entry point with lifespan management
- `database.py` - Database configuration and session management
- `models.py` - SQLAlchemy database models
- `schemas.py` - Pydantic request/response schemas
- `auth.py` - JWT authentication utilities
- `config.py` - Application configuration

### Services
- `llm_service.py` - Multi-provider LLM service with MCP tool integration
- `mcp.py` - Simple MCP integration module (placeholder implementation)

### API Routers
- `routers/auth.py` - Authentication endpoints
- `routers/projects.py` - Project management endpoints
- `routers/chat.py` - Chat conversation endpoints
- `routers/chat_sessions.py` - Chat session management
- `routers/llm_settings.py` - LLM provider configuration
- `routers/mcp.py` - MCP tool management endpoints

### Configuration
- `requirements.txt` - Python dependencies
- `alembic/` - Database migration files

## MCP Integration

The application includes a simple MCP (Model Context Protocol) integration framework:

1. **Simple MCP Module** (mcp.py`): Minimal MCP integration without complex wrappers
2. **Future-Ready**: Placeholder implementation ready for MCP server integration
3. **LangChain Compatibility**: Returns empty tools list until MCP servers are configured

### Current State
- ✅ MCP integration framework in place
- ✅ LangChain tools interface ready
- ⏳ MCP servers not yet implemented (by design)
- ⏳ Tool execution placeholder endpoints

## Development

### Database Operations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### MCP Development
The MCP integration is currently a placeholder implementation. Future development will include:
- MCP server connections
- Tool registration and execution
- Resource management

## Security Features

- JWT token-based authentication
- User-scoped data isolation
- Secure API key storage per user/provider
- Database foreign key constraints
- CORS middleware configuration

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects/` - List user projects
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Chat
- `POST /api/chat/` - Send chat message
- `GET /api/projects/{project_id}/sessions` - List chat sessions
- `POST /api/projects/{project_id}/sessions` - Create chat session

### MCP Tools
- `GET /api/mcp/tools` - List available tools
- `POST /api/mcp/tools/execute` - Execute tool
- `GET /api/mcp/servers/status` - Server status
- `POST /api/mcp/servers/{name}/start` - Start server
- `POST /api/mcp/servers/{name}/stop` - Stop server

### LLM Settings
- `GET /api/llm-settings/` - Get user LLM settings
- `POST /api/llm-settings/` - Create/update LLM settings
- `DELETE /api/llm-settings/{provider}` - Delete provider settings