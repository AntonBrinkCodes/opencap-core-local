from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from mangum import Mangum
import uvicorn
from fastapi.responses import HTMLResponse
from typing import List, Dict


from enum import Enum # Maybe or something else

app = FastAPI()
handler = Mangum(app)



class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections based on client type
        self.active_connections: Dict[str, List[WebSocket]] = {
            "web": [],
            "mobile": []
        }

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        if client_type in self.active_connections:
            self.active_connections[client_type].append(websocket)
        else:
            self.active_connections[client_type] = [websocket]

    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_type: str = None):
        if client_type:
            # Broadcast to a specific type of client
            for connection in self.active_connections[client_type]:
                await connection.send_text(message)
        else:
            # Broadcast to all clients
            for connections in self.active_connections.values():
                for connection in connections:
                    await connection.send_text(message)

    def getNrOfClients(self, client_type: str):
        return len(self.active_connections.get(client_type, []))

        


manager = ConnectionManager()



@app.get("/")
def health_status():
    return {"Hello": "World"}

@app.get("/home")
async def get():
    return HTMLResponse(html)

@app.get("/record_trial")
# Something to start a trial recording. Handled in mobile app.
def testy():
    return {"Start": "Recording"}



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    await manager.connect(websocket, client_type)
    await manager.broadcast(f"Clients connected: {manager.getNrOfClients(client_type)}", client_type)
    try:
        while True:
            data = await websocket.receive_text()
            if client_type == "web":
                # Handle messages from the web app
                await manager.broadcast(f"WebApp says: {data}", "mobile")  # Send to mobile clients
            else:
                # Handle messages from mobile
                await manager.broadcast(f"Mobile says: {data}", "web")  # Send to web app clients
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
        await manager.broadcast(f"Clients connected: {manager.getNrOfClients(client_type)}", client_type)



if __name__=="__main__":
  uvicorn.run(app,host="192.168.0.48",port=8080)