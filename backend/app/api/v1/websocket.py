from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
from app.api.deps import get_current_user
from app.models.user import User as UserModel
from app.services.analytics import AnalyticsService
from app.core.database import get_db
import json
import asyncio

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db = Depends(get_db)
):
    """WebSocket endpoint for real-time updates."""
    try:
        # Verify token and get user
        from app.core.security import decode_token
        payload = decode_token(token)
        
        if not payload:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Get user from database
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=1008, reason="User not found or inactive")
            return
        
        # Connect websocket
        await manager.connect(websocket, user_id)
        
        # Send initial analytics data
        analytics_service = AnalyticsService(db)
        initial_data = analytics_service.get_dashboard_summary()
        await manager.send_personal_message({
            "type": "initial_data",
            "data": initial_data
        }, user_id)
        
        # Keep connection alive and send periodic updates
        try:
            while True:
                # Send periodic analytics updates (every 30 seconds)
                await asyncio.sleep(30)
                updated_data = analytics_service.get_dashboard_summary()
                await manager.send_personal_message({
                    "type": "analytics_update",
                    "data": updated_data
                }, user_id)
                
        except WebSocketDisconnect:
            manager.disconnect(user_id)
            
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))


@router.post("/broadcast")
async def broadcast_message(
    message: dict,
    current_user: UserModel = Depends(get_current_user)
):
    """Broadcast a message to all connected clients (requires authentication)."""
    if not current_user.is_superuser:
        return {"error": "Only superusers can broadcast messages"}
    
    await manager.broadcast(message)
    return {"message": "Message broadcasted successfully"}


@router.post("/notify/{user_id}")
async def notify_user(
    user_id: int,
    message: dict,
    current_user: UserModel = Depends(get_current_user)
):
    """Send a notification to a specific user (requires authentication)."""
    await manager.send_personal_message(message, user_id)
    return {"message": f"Notification sent to user {user_id}"}
