from contextlib import asynccontextmanager

from database import engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import Base
from routers import auth, chat, chat_sessions, llm_settings, mcp, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    Base.metadata.create_all(bind=engine)

    # Initialize MCP (placeholder)
    try:
        from mcp import initialize_mcp

        success = initialize_mcp()
        if success:
            print("MCP initialization ready (no servers configured)")
    except Exception as e:
        print(f"Warning: Failed to initialize MCP: {e}")

    yield

    # Cleanup MCP connections
    try:
        from mcp import cleanup_mcp

        cleanup_mcp()
        print("MCP cleanup completed")
    except Exception as e:
        print(f"Warning: Failed to cleanup MCP: {e}")


app = FastAPI(
    title="LLM Chat App API",
    description="Document assistance LLM chat system for students and researchers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(chat_sessions.router, prefix="/api/projects", tags=["chat-sessions"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(llm_settings.router, prefix="/api/llm-settings", tags=["llm-settings"])
app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp-tools"])


@app.get("/")
async def root():
    return {"message": "LLM Chat App API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/debug/db")
async def debug_db():
    """Debug endpoint to check database connection and tables"""
    from database import engine
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))

            # Get tables
            result = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in result.fetchall()]

            return {"status": "success", "database_connected": True, "tables": tables}
    except Exception as e:
        return {"status": "error", "database_connected": False, "error": str(e)}
