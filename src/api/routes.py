from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal

from src.llms.chains.chain import ChainManagement
from src.llms.model import ModelManagement
from src.llms.memory import MemoryManagement
from src.utils.ids import generate_session_id, generate_user_id
from .dependencies import get_model

router = APIRouter()

@router.get("/sessions")
async def list_sessions(user_id: str):
    """
    List all chat sessions for a user, with session_id and session_name.
    """
    try:
        memory = MemoryManagement(user_id=user_id)
        # Query all unique session_ids and their latest session_name for this user
        from src.llms.utils.db_config import DatabaseConfig
        db_config = DatabaseConfig()
        with db_config.get_connection() as conn:
            cursor = conn.execute('''
                SELECT session_id, MAX(timestamp), session_name, mode
                FROM chat_message
                WHERE user_id = ?
                GROUP BY session_id, mode
                ORDER BY MAX(timestamp) DESC
            ''', (user_id,))
            sessions = [
                {"session_id": row[0], "session_name": row[2], "mode": row[3]} for row in cursor.fetchall()
            ]
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID")
    mode: Literal['consultant', 'docs_writer'] = Field('consultant', description="Chatbot mode")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    mode: str

class SessionRequest(BaseModel):
    user_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    user_id: str

class HistoryResponse(BaseModel):
    messages: list
    session_id: str
    user_id: str
    last_mode: str = None

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, model: ModelManagement = Depends(get_model)):
    """
    Send a message to the chatbot and get a response.
    """
    try:
        # Generate IDs if not provided
        session_id = request.session_id or generate_session_id()
        user_id = request.user_id or generate_user_id()
        
        print(f"DEBUG API: session_id={session_id}, user_id={user_id}, mode={request.mode}")
        print(f"DEBUG API: message={request.message}")
        print(f"DEBUG API: model type={type(model)}")
        
        # Initialize chain
        chain = ChainManagement(
            mode=request.mode,
            session_id=session_id,
            user_id=user_id,
            model=model
        )
        
        print(f"DEBUG API: chain created successfully")
        
        # Get response - chain.invoke expects a string
        response = chain.invoke(request.message)
        
        print(f"DEBUG API: response received: {response}")
        
        return ChatResponse(
            response=response,
            session_id=session_id,
            user_id=user_id,
            mode=request.mode
        )
    except Exception as e:
        print(f"DETAILED ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"FULL TRACEBACK:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/session/new", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new chat session.
    """
    session_id = generate_session_id()
    user_id = request.user_id or generate_user_id()
    
    return SessionResponse(
        session_id=session_id,
        user_id=user_id
    )

@router.get("/session/{session_id}/history", response_model=HistoryResponse)
async def get_history(session_id: str, user_id: str, mode: str = "consultant"):
    """
    Get chat history for a session with specific mode.
    """
    try:
        memory = MemoryManagement(session_id=session_id, user_id=user_id, mode=mode)
        memory.get_messages()
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "additional_kwargs": msg.additional_kwargs,
                "mode": getattr(msg, 'mode', None)  # in case mode is attached to message
            }
            for msg in memory.message
        ]
        # Fetch the mode of the last message in the session (regardless of mode param)
        import sqlite3
        last_mode = None
        try:
            with memory.db_config.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT mode FROM chat_message WHERE session_id = ? AND user_id = ? ORDER BY timestamp DESC LIMIT 1",
                    (session_id, user_id)
                )
                row = cursor.fetchone()
                if row:
                    last_mode = row[0]
        except sqlite3.Error:
            last_mode = None
        return HistoryResponse(
            messages=messages,
            session_id=session_id,
            user_id=user_id,
            last_mode=last_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@router.get("/session/{session_id}/name")
async def get_session_name(session_id: str, user_id: str, mode: str = "consultant"):
    """
    Get session name for specific mode.
    """
    try:
        memory = MemoryManagement(session_id=session_id, user_id=user_id, mode=mode)
        session_name = memory.get_session_name(session_id, user_id, mode)
        return {"session_name": session_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session name: {str(e)}")

@router.delete("/session/{session_id}/clear")
async def clear_history(session_id: str, user_id: str, mode: str = "consultant"):
    """
    Clear chat history for a session with specific mode.
    """
    try:
        memory = MemoryManagement(session_id=session_id, user_id=user_id, mode=mode)
        memory.clear()
        return {"message": "History cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")
