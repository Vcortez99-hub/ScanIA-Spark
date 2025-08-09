"""
WebSocket endpoints for real-time communication

Provides WebSocket connections for:
- Real-time scan progress updates
- Live vulnerability notifications
- System status updates
"""

import json
import asyncio
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from fastapi.routing import APIRouter

from app.api.v1.auth import get_current_user_websocket
from app.models.user import User
from app.core.logging_simple import get_logger

logger = get_logger(__name__)

# WebSocket router
router = APIRouter(prefix="/ws", tags=["websockets"])


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Maintains active connections per user and provides methods for
    sending targeted and broadcast messages.
    """
    
    def __init__(self):
        # Active connections by user ID
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Scan subscriptions: scan_id -> set of user_ids
        self.scan_subscriptions: Dict[str, Set[str]] = {}
        
        # User scan subscriptions: user_id -> set of scan_ids
        self.user_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.user_subscriptions.setdefault(user_id, set())
        
        logger.info(f"WebSocket connected for user {user_id}")
        
        # Send welcome message
        await self.send_personal_message(user_id, {
            "type": "connection_established",
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection and cleanup subscriptions"""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                
                # Remove user if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    
                    # Clean up subscriptions
                    if user_id in self.user_subscriptions:
                        for scan_id in self.user_subscriptions[user_id]:
                            if scan_id in self.scan_subscriptions:
                                self.scan_subscriptions[scan_id].discard(user_id)
                                if not self.scan_subscriptions[scan_id]:
                                    del self.scan_subscriptions[scan_id]
                        
                        del self.user_subscriptions[user_id]
                
            except ValueError:
                pass
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, user_id: str, message: Dict):
        """Send message to all connections of a specific user"""
        if user_id in self.active_connections:
            message_text = json.dumps(message)
            
            # Send to all user connections
            disconnected_websockets = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message_text)
                except Exception as e:
                    logger.warning(f"Failed to send message to user {user_id}: {str(e)}")
                    disconnected_websockets.append(websocket)
            
            # Clean up failed connections
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)
    
    async def send_scan_update(self, scan_id: str, message: Dict):
        """Send scan update to all subscribed users"""
        if scan_id in self.scan_subscriptions:
            for user_id in self.scan_subscriptions[scan_id]:
                await self.send_personal_message(user_id, {
                    **message,
                    "scan_id": scan_id
                })
    
    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected users"""
        message_text = json.dumps(message)
        
        disconnected_users = []
        for user_id, websockets in self.active_connections.items():
            disconnected_websockets = []
            
            for websocket in websockets:
                try:
                    await websocket.send_text(message_text)
                except Exception:
                    disconnected_websockets.append(websocket)
            
            # Clean up failed connections
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)
    
    def subscribe_to_scan(self, user_id: str, scan_id: str):
        """Subscribe user to scan progress updates"""
        # Add to scan subscriptions
        if scan_id not in self.scan_subscriptions:
            self.scan_subscriptions[scan_id] = set()
        self.scan_subscriptions[scan_id].add(user_id)
        
        # Add to user subscriptions
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(scan_id)
        
        logger.info(f"User {user_id} subscribed to scan {scan_id}")
    
    def unsubscribe_from_scan(self, user_id: str, scan_id: str):
        """Unsubscribe user from scan updates"""
        # Remove from scan subscriptions
        if scan_id in self.scan_subscriptions:
            self.scan_subscriptions[scan_id].discard(user_id)
            if not self.scan_subscriptions[scan_id]:
                del self.scan_subscriptions[scan_id]
        
        # Remove from user subscriptions  
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(scan_id)
        
        logger.info(f"User {user_id} unsubscribed from scan {scan_id}")
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "connected_users": len(self.active_connections),
            "active_scan_subscriptions": len(self.scan_subscriptions),
            "total_subscriptions": sum(len(subs) for subs in self.user_subscriptions.values())
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/scan-progress/{scan_id}")
async def websocket_scan_progress(
    websocket: WebSocket,
    scan_id: str,
    current_user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for real-time scan progress updates.
    
    Clients can connect to this endpoint to receive live updates
    about scan progress, status changes, and results.
    """
    user_id = str(current_user.id)
    
    await manager.connect(websocket, user_id)
    
    # Subscribe to scan updates
    manager.subscribe_to_scan(user_id, scan_id)
    
    try:
        # Send initial scan status
        await manager.send_personal_message(user_id, {
            "type": "scan_subscription_confirmed",
            "scan_id": scan_id,
            "message": f"Subscribed to scan progress for {scan_id}",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                message_type = message.get("type")
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message_type == "request_status":
                    # Client requesting current scan status
                    await manager.send_personal_message(user_id, {
                        "type": "status_requested",
                        "scan_id": scan_id,
                        "message": "Status update requested",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket client")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {str(e)}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}, scan {scan_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}, scan {scan_id}: {str(e)}")
    
    finally:
        # Clean up
        manager.unsubscribe_from_scan(user_id, scan_id)
        manager.disconnect(websocket, user_id)


@router.websocket("/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user_websocket)
):
    """
    WebSocket endpoint for general notifications.
    
    Provides real-time notifications about:
    - Scan completions
    - System alerts
    - Account updates
    """
    user_id = str(current_user.id)
    
    await manager.connect(websocket, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(user_id, {
            "type": "notifications_connected",
            "message": "Connected to notification stream",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket client")
            except Exception as e:
                logger.error(f"Error handling notification WebSocket message: {str(e)}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Notifications WebSocket disconnected for user {user_id}")
    
    except Exception as e:
        logger.error(f"Notifications WebSocket error for user {user_id}: {str(e)}")
    
    finally:
        manager.disconnect(websocket, user_id)


# Helper functions for sending updates from other parts of the application

async def send_scan_progress_update(scan_id: str, progress: float, message: str):
    """
    Send scan progress update to subscribed users.
    
    Args:
        scan_id: Scan ID
        progress: Progress percentage (0-100)
        message: Progress message
    """
    await manager.send_scan_update(scan_id, {
        "type": "scan_progress",
        "progress": progress,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })


async def send_scan_status_change(scan_id: str, status: str, message: str = None):
    """
    Send scan status change notification.
    
    Args:
        scan_id: Scan ID
        status: New status
        message: Optional status message
    """
    await manager.send_scan_update(scan_id, {
        "type": "scan_status_change", 
        "status": status,
        "message": message or f"Scan status changed to {status}",
        "timestamp": datetime.utcnow().isoformat()
    })


async def send_scan_completed(scan_id: str, vulnerability_count: int, duration_seconds: float):
    """
    Send scan completion notification.
    
    Args:
        scan_id: Scan ID
        vulnerability_count: Number of vulnerabilities found
        duration_seconds: Scan duration
    """
    await manager.send_scan_update(scan_id, {
        "type": "scan_completed",
        "vulnerability_count": vulnerability_count,
        "duration_seconds": duration_seconds,
        "message": f"Scan completed: {vulnerability_count} vulnerabilities found in {duration_seconds:.1f}s",
        "timestamp": datetime.utcnow().isoformat()
    })


async def send_vulnerability_found(scan_id: str, vulnerability: Dict):
    """
    Send real-time vulnerability notification.
    
    Args:
        scan_id: Scan ID
        vulnerability: Vulnerability data
    """
    await manager.send_scan_update(scan_id, {
        "type": "vulnerability_found",
        "vulnerability": vulnerability,
        "message": f"New {vulnerability.get('severity', 'unknown')} vulnerability found: {vulnerability.get('title', 'Unknown')}",
        "timestamp": datetime.utcnow().isoformat()
    })


async def send_user_notification(user_id: str, notification_type: str, message: str, data: Dict = None):
    """
    Send notification to specific user.
    
    Args:
        user_id: User ID
        notification_type: Type of notification
        message: Notification message
        data: Additional data
    """
    await manager.send_personal_message(user_id, {
        "type": notification_type,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    })


async def broadcast_system_notification(message: str, notification_type: str = "system_alert"):
    """
    Broadcast system-wide notification.
    
    Args:
        message: Notification message
        notification_type: Type of notification
    """
    await manager.broadcast_message({
        "type": notification_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })


def get_websocket_stats() -> Dict:
    """Get WebSocket connection statistics"""
    return manager.get_connection_stats()