from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models import User, Project, ChatSession, ChatLog
from schemas import (
    ChatSessionCreate, 
    ChatSessionUpdate, 
    ChatSession as ChatSessionSchema,
    ChatSessionWithStats
)
from auth import get_current_user
import uuid

router = APIRouter()


@router.post("/{project_id}/sessions", response_model=ChatSessionSchema)
def create_chat_session(
    project_id: uuid.UUID,
    session: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session in a project"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create new session
    db_session = ChatSession(
        project_id=project_id,
        title=session.title or "New Chat"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/{project_id}/sessions", response_model=List[ChatSessionWithStats])
def get_chat_sessions(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat sessions for a project with message counts and previews"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get sessions with statistics
    sessions = db.query(
        ChatSession,
        func.count(ChatLog.id).label('message_count'),
        func.max(ChatLog.created_at).label('last_message_time')
    ).outerjoin(ChatLog).filter(
        ChatSession.project_id == project_id
    ).group_by(ChatSession.id).order_by(desc(ChatSession.updated_at)).all()
    
    # Build response with statistics and previews
    result = []
    for session, message_count, last_message_time in sessions:
        # Get last message preview
        last_message = db.query(ChatLog).filter(
            ChatLog.session_id == session.id
        ).order_by(desc(ChatLog.created_at)).first()
        
        last_message_preview = None
        if last_message:
            # Truncate content to 100 characters
            content = last_message.content
            if len(content) > 100:
                content = content[:97] + "..."
            last_message_preview = f"{last_message.role}: {content}"
        
        result.append(ChatSessionWithStats(
            id=session.id,
            project_id=session.project_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count or 0,
            last_message_preview=last_message_preview
        ))
    
    return result


@router.get("/{project_id}/sessions/{session_id}", response_model=ChatSessionSchema)
def get_chat_session(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    return session


@router.put("/{project_id}/sessions/{session_id}", response_model=ChatSessionSchema)
def update_chat_session(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    session_update: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Update session
    update_data = session_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    return session


@router.delete("/{project_id}/sessions/{session_id}")
def delete_chat_session(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and all its messages"""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.project_id == project_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete session (cascade will delete chat logs)
    db.delete(session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}