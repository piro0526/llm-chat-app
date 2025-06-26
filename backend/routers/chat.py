from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, Project, ChatLog, ChatSession, LLMSetting
from schemas import ChatRequest, ChatResponse, ChatLog as ChatLogSchema
from auth import get_current_user
from llm_service import llm_service
import uuid

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify session exists and get project
    session = db.query(ChatSession).filter(
        ChatSession.id == request.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == session.project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get user's LLM settings
    llm_setting = db.query(LLMSetting).filter(
        LLMSetting.user_id == current_user.id,
        LLMSetting.provider == request.provider
    ).first()
    
    if not llm_setting:
        raise HTTPException(
            status_code=400,
            detail=f"LLM settings not found for provider: {request.provider}"
        )
    
    # Get chat history for context (from this session only)
    chat_history = db.query(ChatLog).filter(
        ChatLog.session_id == request.session_id
    ).order_by(ChatLog.created_at.desc()).limit(10).all()
    chat_history = list(reversed(chat_history))
    
    try:
        # Save user message
        user_message = ChatLog(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        
        # Update session timestamp
        from sqlalchemy import func
        session.updated_at = func.now()
        db.commit()
        
        # Get available MCP tools
        mcp_tools = llm_service.get_mcp_tools()
        
        # Generate AI response
        response = await llm_service.generate_response(
            message=request.message,
            provider=request.provider,
            api_key=llm_setting.api_key,
            model_name=request.model or llm_setting.model,
            chat_history=chat_history,
            tools=mcp_tools
        )
        
        # Save AI response
        ai_message = ChatLog(
            session_id=request.session_id,
            role="assistant",
            content=response
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        return ChatResponse(message=response, chat_log_id=ai_message.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.get("/sessions/{session_id}/history", response_model=List[ChatLogSchema])
def get_session_history(
    session_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify session exists and get project
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == session.project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chat_logs = db.query(ChatLog).filter(
        ChatLog.session_id == session_id
    ).order_by(ChatLog.created_at.asc()).offset(skip).limit(limit).all()
    
    return chat_logs


@router.delete("/sessions/{session_id}/history")
def clear_session_history(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify session exists and get project
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == session.project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.query(ChatLog).filter(ChatLog.session_id == session_id).delete()
    db.commit()
    
    return {"message": "Session chat history cleared successfully"}