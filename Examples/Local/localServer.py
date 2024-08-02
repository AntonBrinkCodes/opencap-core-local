from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from mangum import Mangum
import uvicorn
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional
import logging
from sessionModel import Session, Trial, Subject

from enum import Enum # Maybe or something else

app = FastAPI()
handler = Mangum(app)

import socket

class sessionManager:
    def __init__(self):
        self.sessions: List[Session] = []
        self.activeSession: Optional[Session] = None
    
    def addSession(self, session: Session):
        self.sessions.append(session)
        self.activeSession = session
    
    def removeSession(self, session):
        self.sessions.remove(session)
        if self.activeSession == session:
            self.activeSession = None

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
        logger.debug("Removing client with type: "+client_type)
        self.active_connections[client_type].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_type: str = None):
        if client_type:
            # Broadcast to a specific type of client
            for connection in self.active_connections[client_type]:
                await self.trySendMessage(connection, message)
        else:
            # Broadcast to all clients
            for connections in self.active_connections.values():
                for connection in connections:
                    await self.trySendMessage(connection, message)

    def getNrOfClients(self, client_type: str):
        return len(self.active_connections.get(client_type, []))
    
    async def trySendMessage(self, connection: WebSocket, message: str):
        if not connection.client_state == WebSocketState.CONNECTED:
            return
        try:
            await connection.send_text(message)
        except RuntimeError as e:
            print(f"Error sending message: {e}")

    #   Function to find the index of a WebSocket in a given client type 
    def find_websocket_index(self, client_type: str, websocket: WebSocket) -> int:
        if client_type in self.active_connections:
            try:
                # Directly access the list associated with client_type and find the index of websocket
                return self.active_connections[client_type].index(websocket)
            except ValueError:
                return -1  # Return -1 if the WebSocket is not found
        else:
            raise KeyError(f"Client type '{client_type}' not found in active connections")

        
        
'''sync def broadcast(self, message: str, client_type: str):
        for connection in self.active_connections[client_type]:
            if not connection.client_state == WebSocketState.CONNECTED:
                continue
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"Error sending message: {e}")'''
        


manager = ConnectionManager()
logger = logging.getLogger('uvicorn.error')
sessionManager = sessionManager()


@app.get("/")
def health_status():
    return {"Hello": "World"}

@app.get("/record_trial")
# Something to start a trial recording. Handled in mobile app.
def testy():
    return {"Start": "Recording"}



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    await manager.connect(websocket, client_type)
    logger.debug(f"Clients connected: {manager.getNrOfClients(client_type)}")
    await manager.broadcast(f"Web-apps connected: {manager.getNrOfClients("web")}\n Cameras connected: {manager.getNrOfClients("mobile")}")
    try:
        while True:
            
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                break

            if data["type"] == "websocket.receive":
                if "text" in data:
                    message = data["text"]
                    if client_type == "web":
                        if message =="newSession":
                            # Create new session
                            print("creating new session")
                            sessionManager.addSession(Session())
                            sessionID = sessionManager.activeSession.getID()
                            await manager.send_personal_message(f"New session id: {sessionID} ", websocket)
                        else:
                            await manager.broadcast(f"WebApp says: {message}", "mobile")
                    else:
                        await manager.broadcast(f"Mobile says: {message}", "web")

                elif "bytes" in data:
                    binary_data = data["bytes"]
                    # Handle binary data here
                    print(f"Received binary data: {len(binary_data)} bytes")
                    # You could save the binary data to a file, process it, etc.
                    binary_data = data["bytes"]
                    # Save binary data to a file
                    # TODO: Make a filemanager for this
                    save_binary_file(binary_data, f"received_file_cam{manager.find_websocket_index(client_type,websocket)}.mov")
                    # Optionally broadcast the receipt
                    await manager.broadcast(f"Received binary data of size: {len(binary_data)} bytes")
            
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, client_type)
        logger.debug("A client is disconnecting")
        await manager.broadcast(f"Web-apps connected: {manager.getNrOfClients("web")}, Cameras connected: {manager.getNrOfClients("mobile")}")

def save_binary_file(data: bytes, filename: str):
    with open(filename, 'wb') as file:
        file.write(data)
    print(f"File saved as {filename}")


if __name__=="__main__":
    hostname = socket.gethostname()    
    print(f"Hostname: {hostname}")

    ip_address = "192.168.0.48"#socket.gethostbyname(hostname)
    print(f"IP Address: {ip_address}")
    uvicorn.run(app,host=ip_address,port=8080)