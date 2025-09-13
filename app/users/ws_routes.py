from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
from typing import Dict, List, Any, Optional
import asyncio
from app.auth.services import SECRET_KEY, ALGORITHM

ws_router = APIRouter(prefix="/ws", tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        # Diccionario: {user_id: [lista de websockets]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Event loop principal para enviar mensajes desde hilos
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: Any, user_id: int):
        """Enviar mensaje solo a un usuario específico"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                if isinstance(message, (dict, list)):
                    await connection.send_json(message)
                else:
                    await connection.send_text(str(message))

    async def broadcast(self, message: Any):
        """Enviar mensaje a todos los usuarios conectados"""
        for connections in self.active_connections.values():
            for connection in connections:
                if isinstance(message, (dict, list)):
                    await connection.send_json(message)
                else:
                    await connection.send_text(str(message))

manager = ConnectionManager()

@ws_router.websocket("/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket para notificaciones en tiempo real.
    El cliente se conecta con:
    ws://localhost:8001/ws/notifications?token=<JWT>
    """
    try:
        # 🔑 Decodificar JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")

        if not user_id:
            await websocket.close(code=4001)
            return

    except JWTError:
        await websocket.close(code=4002)
        return

    # Guardar el event loop activo para permitir envíos desde contextos síncronos
    manager.loop = asyncio.get_running_loop()
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Escuchar mensajes entrantes (opcional)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
