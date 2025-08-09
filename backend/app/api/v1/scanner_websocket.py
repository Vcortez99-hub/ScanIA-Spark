"""
Scanner WebSocket endpoints for real-time progress tracking
"""

import asyncio
import json
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.api.v1.auth import get_current_user_from_token
from app.models.user import User
from app.models.scan import Scan
from app.core.logging_simple import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class WebSocketManager:
    """Manages WebSocket connections for scan progress tracking"""
    
    def __init__(self):
        # Dictionary of scan_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Dictionary of scan_id -> latest progress data
        self.latest_progress: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket, scan_id: str):
        """Connect a WebSocket to a specific scan"""
        await websocket.accept()
        
        if scan_id not in self.active_connections:
            self.active_connections[scan_id] = []
        
        self.active_connections[scan_id].append(websocket)
        logger.info(f"WebSocket connected to scan {scan_id}. Total connections: {len(self.active_connections[scan_id])}")
        
        # Send latest progress if available
        if scan_id in self.latest_progress:
            try:
                await websocket.send_text(json.dumps(self.latest_progress[scan_id]))
            except Exception as e:
                logger.warning(f"Failed to send latest progress to new connection: {e}")
    
    def disconnect(self, websocket: WebSocket, scan_id: str):
        """Disconnect a WebSocket from a scan"""
        if scan_id in self.active_connections:
            try:
                self.active_connections[scan_id].remove(websocket)
                logger.info(f"WebSocket disconnected from scan {scan_id}")
                
                # Clean up empty connection lists
                if not self.active_connections[scan_id]:
                    del self.active_connections[scan_id]
                    logger.info(f"No more connections for scan {scan_id}, cleaning up")
                    
            except ValueError:
                # WebSocket was not in the list
                pass
    
    async def send_progress_update(self, scan_id: str, progress_data: Dict):
        """Send progress update to all connected WebSockets for a scan"""
        if scan_id not in self.active_connections:
            return
        
        # Store latest progress
        self.latest_progress[scan_id] = progress_data
        
        # Send to all connected clients
        connections_to_remove = []
        
        for websocket in self.active_connections[scan_id].copy():
            try:
                await websocket.send_text(json.dumps(progress_data))
            except Exception as e:
                logger.warning(f"Failed to send progress update to WebSocket: {e}")
                connections_to_remove.append(websocket)
        
        # Remove failed connections
        for websocket in connections_to_remove:
            self.disconnect(websocket, scan_id)
    
    def get_connection_count(self, scan_id: str) -> int:
        """Get number of active connections for a scan"""
        return len(self.active_connections.get(scan_id, []))
    
    def get_total_connections(self) -> int:
        """Get total number of active WebSocket connections"""
        return sum(len(connections) for connections in self.active_connections.values())
    
    def cleanup_scan(self, scan_id: str):
        """Clean up all connections and data for a completed scan"""
        if scan_id in self.active_connections:
            # Close all connections
            for websocket in self.active_connections[scan_id]:
                try:
                    asyncio.create_task(websocket.close())
                except Exception:
                    pass
            
            del self.active_connections[scan_id]
        
        if scan_id in self.latest_progress:
            del self.latest_progress[scan_id]
        
        logger.info(f"Cleaned up WebSocket data for scan {scan_id}")


# Global WebSocket manager
ws_manager = WebSocketManager()


async def verify_scan_access(scan_id: str, user: User, db: AsyncSession) -> bool:
    """Verify user has access to the scan"""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(Scan).where(Scan.id == scan_id, Scan.user_id == user.id)
        )
        scan = result.scalar_one_or_none()
        return scan is not None
    except Exception as e:
        logger.error(f"Error verifying scan access: {e}")
        return False


@router.websocket("/scan/{scan_id}/progress")
async def websocket_scan_progress(
    websocket: WebSocket,
    scan_id: str,
    token: str = Query(..., description="JWT authentication token"),
):
    """
    WebSocket endpoint for real-time scan progress updates
    
    Args:
        scan_id: ID of the scan to monitor
        token: JWT authentication token passed as query parameter
    """
    logger.info(f"WebSocket connection attempt for scan {scan_id}")
    
    try:
        # Authenticate user
        try:
            user = await get_current_user_from_token(token)
            logger.info(f"WebSocket authenticated user: {user.email}")
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Get database session (simplified approach for WebSocket)
        from app.core.database import get_async_session
        async with get_async_session() as db:
            # Verify scan access
            if not await verify_scan_access(scan_id, user, db):
                logger.warning(f"User {user.email} denied access to scan {scan_id}")
                await websocket.close(code=4004, reason="Scan not found or access denied")
                return
        
        # Connect to WebSocket manager
        await ws_manager.connect(websocket, scan_id)
        
        try:
            while True:
                # Keep connection alive and listen for client messages
                try:
                    # Wait for messages from client (ping/pong, etc.)
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    # Handle client messages
                    try:
                        data = json.loads(message)
                        message_type = data.get('type')
                        
                        if message_type == 'ping':
                            # Respond to ping with pong
                            await websocket.send_text(json.dumps({
                                'type': 'pong',
                                'timestamp': asyncio.get_event_loop().time()
                            }))
                            
                        elif message_type == 'request_status':
                            # Send current progress if available
                            if scan_id in ws_manager.latest_progress:
                                await websocket.send_text(
                                    json.dumps(ws_manager.latest_progress[scan_id])
                                )
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received from WebSocket client: {message}")
                        
                except asyncio.TimeoutError:
                    # Send periodic heartbeat
                    try:
                        await websocket.send_text(json.dumps({
                            'type': 'heartbeat',
                            'timestamp': asyncio.get_event_loop().time(),
                            'scan_id': scan_id
                        }))
                    except Exception:
                        break  # Connection is dead
                        
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected from scan {scan_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error for scan {scan_id}: {e}")
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except Exception:
            pass
    finally:
        # Clean up connection
        ws_manager.disconnect(websocket, scan_id)


# Progress update functions to be called by scan engines

async def broadcast_scan_progress(
    scan_id: str,
    progress: float,
    message: str,
    scanner_type: str = None,
    scanner_progress: Dict[str, float] = None,
    status: str = "running"
):
    """
    Broadcast progress update to all connected WebSocket clients
    
    Args:
        scan_id: Scan ID
        progress: Overall progress percentage (0-100)
        message: Progress message
        scanner_type: Type of scanner currently running
        scanner_progress: Progress of individual scanners
        status: Scan status
    """
    try:
        progress_data = {
            'type': 'progress_update',
            'scan_id': scan_id,
            'overall_progress': progress,
            'message': message,
            'status': status,
            'timestamp': asyncio.get_event_loop().time(),
            'scanner_type': scanner_type,
            'scanner_progress': scanner_progress or {}
        }
        
        await ws_manager.send_progress_update(scan_id, progress_data)
        logger.debug(f"Broadcasted progress update for scan {scan_id}: {progress:.1f}%")
        
    except Exception as e:
        logger.error(f"Failed to broadcast progress update for scan {scan_id}: {e}")


async def broadcast_scan_completion(
    scan_id: str,
    status: str,
    message: str,
    vulnerability_summary: Dict = None,
    duration_seconds: int = None
):
    """
    Broadcast scan completion to all connected WebSocket clients
    
    Args:
        scan_id: Scan ID
        status: Final scan status (completed, failed, cancelled)
        message: Completion message
        vulnerability_summary: Summary of found vulnerabilities
        duration_seconds: Total scan duration
    """
    try:
        completion_data = {
            'type': 'scan_completion',
            'scan_id': scan_id,
            'status': status,
            'message': message,
            'overall_progress': 100.0 if status == 'completed' else 0.0,
            'timestamp': asyncio.get_event_loop().time(),
            'vulnerability_summary': vulnerability_summary or {},
            'duration_seconds': duration_seconds
        }
        
        await ws_manager.send_progress_update(scan_id, completion_data)
        logger.info(f"Broadcasted completion for scan {scan_id}: {status}")
        
        # Clean up after a delay to allow clients to receive the message
        asyncio.create_task(cleanup_scan_after_delay(scan_id, delay=30))
        
    except Exception as e:
        logger.error(f"Failed to broadcast completion for scan {scan_id}: {e}")


async def cleanup_scan_after_delay(scan_id: str, delay: int = 30):
    """Clean up WebSocket data for a scan after a delay"""
    await asyncio.sleep(delay)
    ws_manager.cleanup_scan(scan_id)


# Health check endpoint for WebSocket manager

@router.get("/stats")
async def websocket_stats():
    """Get WebSocket manager statistics"""
    return {
        "total_connections": ws_manager.get_total_connections(),
        "active_scans": len(ws_manager.active_connections),
        "scans_with_progress": len(ws_manager.latest_progress)
    }