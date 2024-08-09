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
        # Dictionary to store active connections based on session ID and client type
        self.session_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        # Dictionary to store general connections (no session ID)
        self.general_connections: Dict[str, List[WebSocket]] = {
            "web": [],
            "mobile": []
        }

    async def connect(self, websocket: WebSocket, client_type: str, session_id: Optional[str] = None):
        await websocket.accept()
        if session_id:
            # Handle session-specific connections
            if session_id not in self.session_connections:
                self.session_connections[session_id] = {
                    "web": [],
                    "mobile": []
                }
            self.session_connections[session_id][client_type].append(websocket)
        else:
            # Handle general connections
            self.general_connections[client_type].append(websocket)

    def disconnect(self, websocket: WebSocket, client_type: str, session_id: Optional[str] = None):
        if session_id:
            # Remove from session-specific connections
            if session_id in self.session_connections:
                self.session_connections[session_id][client_type].remove(websocket)
        else:
            # Remove from general connections
            self.general_connections[client_type].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_type: str = None, session_id: Optional[str] = None):
        if session_id:
            print(f"trying to broadcast to {session_id}")
            # Broadcast to a specific session
            print(self.session_connections)
            if session_id in self.session_connections:
                print(f"{session_id} is in self.session_connections!")
                if client_type:
                    for connection in self.session_connections[session_id][client_type]:
                        print(f"Sending {message} to {client_type} in {session_id}")
                        await self.trySendMessage(connection, message)
                else:
                    for connections in self.session_connections[session_id].values():
                        for connection in connections:
                            await self.trySendMessage(connection, message)
        else:
            # Broadcast to all clients in the general connections
            if client_type:
                for connection in self.general_connections[client_type]:
                    await self.trySendMessage(connection, message)
            else:
                for connections in self.general_connections.values():
                    for connection in connections:
                        await self.trySendMessage(connection, message)

    def getNrOfClients(self, client_type: str, session_id: Optional[str] = None):
        if session_id:
            return len(self.session_connections.get(session_id, {}).get(client_type, []))
        else:
            return len(self.general_connections.get(client_type, []))

    async def trySendMessage(self, connection: WebSocket, message: str):
        if not connection.client_state == WebSocketState.CONNECTED:
            return
        try:
            await connection.send_text(message)
        except RuntimeError as e:
            print(f"Error sending message: {e}")

    def find_websocket_index(self, client_type: str, websocket: WebSocket) -> int:
        # Check general connections first
        if client_type in self.general_connections:
            try:
                return self.general_connections[client_type].index(websocket)
            except ValueError:
                pass
        
        # Then check session connections
        for session_id, client_types in self.session_connections.items():
            if client_type in client_types:
                try:
                    return client_types[client_type].index(websocket)
                except ValueError:
                    pass
        return -1

        
        
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
    await manager.broadcast(f"General Web-apps connected: {manager.getNrOfClients('web')}\n"
                            f"General Cameras connected: {manager.getNrOfClients('mobile')}", client_type)
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
                            print(f"previous sessions are:")
                            for session in sessionManager.sessions:
                                print(session.getID())
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


'''
SESSION WEBSOCKET
'''
@app.websocket("/ws/{session_id}/session")
async def websocket_endpoint(websocket: WebSocket, session_id: str, client_type: str):
    await manager.connect(websocket, client_type, session_id=session_id)
    print(f"BROADCASTING: Session {session_id} mobiles connected: {manager.getNrOfClients(client_type="mobile", session_id=session_id)}")
    await manager.broadcast(f"Session {session_id} mobiles connected: {manager.getNrOfClients(client_type="mobile", session_id=session_id)}", session_id=session_id)
    try:
        while True:
            
            data = await websocket.receive()
            print(f"received message in {session_id}")
            if data["type"] == "websocket.disconnect":
                break

            if data["type"] == "websocket.receive":
                if "text" in data:
                    message = data["text"]
                    print(data)
                    if client_type == "web":
                        if message =="newSession":
                            # Create new session
                            print("creating new session")
                            sessionManager.addSession(Session())
                            sessionID = sessionManager.activeSession.getID()
                            await manager.send_personal_message(f"New session id: {sessionID} ", websocket)
                        else:
                            print(f"Session {session_id} says: {message}")
                            await manager.broadcast(f"Session {session_id} says: {message}", "mobile", session_id=session_id)
                    else:
                        await manager.broadcast(f"Session {session_id} Mobile says: {message}", "web", session_id=session_id)

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
        manager.disconnect(websocket, client_type, session_id=session_id)
        logger.debug("A client is disconnecting")
        await manager.broadcast(f"Session {session_id} Web-apps connected: {manager.getNrOfClients("web")}, Cameras connected: {manager.getNrOfClients("mobile")}", session_id=session_id)


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