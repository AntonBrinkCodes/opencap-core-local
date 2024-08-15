from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from mangum import Mangum
import uvicorn
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional
import logging
from sessionModel import Session, Trial, Subject
import json
import base64


import threading
import time
import asyncio

from enum import Enum # Maybe or something else

app = FastAPI()
handler = Mangum(app)

import socket
                
                
class CustomError(Exception):
    pass


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
    
    # Should do this a better way maybe
    def findSessionByID(self, session_id: str) -> Optional[Session]:
        for session in self.sessions:
            if str(session.getID()) == session_id:
                return session
        return None
    
    async def sendStartTrial(self, session_id: str, trialType: Optional[str] = "dynamic"):
        message = {
            "command": "start",
            "trialType": trialType,
            "content": '',
            "session_id": session_id
            }
        json_message = json.dumps(message)
        await manager.broadcast(message=json_message, client_type="mobile", session_id = session_id)
    
    async def sendStopTrial(self, session_id: str):
        message = {
            "command": "stop",
            "content": '',
            "trialType": '',
            "session_id": ''
        }
        json_message = json.dumps(message)
        await manager.broadcast(message = json_message, client_type="mobile", session_id=session_id)
    
    async def startTrial(self, session: Session, trialType: Optional[str] = "dynamic", process=True):
        '''
            Creates a new trial in the Session.
            Starts the trials by:
                Telling all mobiles in the session to start recording.
                If trialType is static or calibration stops the recordings after 1s.
                saves the videos.
                if process is True then calls the backend to process the videos.

            Parameters:
                session (Session): The session that the trial is in.
                trialType Optional[str]: The type of trial (calibration, static, dynamic). Default is dynamic.
                process (Boolean): Whetever to process the trial immediatly or not.

            Returns:
                Some info whetever the trial successfully processed/uploaded.
        '''
        print("running {trialType} trial")
        session_id = str(session.getID())
        try:
            #Start recording
            await manager.broadcast(f"Toast: info: Recording calibration...", session_id=session_id)
            await self.sendStartTrial(session_id = session_id, trialType=trialType)
            if trialType == 'calibration' or trialType == 'static':
                # Stop recording automatically after 1 second.
                await asyncio.sleep(1)
                await self.sendStopTrial(session_id=session_id)
                await manager.broadcast(f"Toast: success: Succesfully finished recording :)")
            #Upload files
            if process:
                
                raise CustomError("Process not implemented yet")
                #Process files
        except CustomError as e:
            await manager.broadcast(f"Toast: error: {e}", client_type="web", session_id=session.getID())
        else:
            #Successfully processed trial
            sessionID = str(session.getID())
            await manager.broadcast(f"Toast: success: BABY", client_type="web", session_id=sessionID)

        # Run a trial, can be calibration. static, or dynamic.

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

    async def broadcast(self, message: str, client_type: Optional[str] = None, session_id: Optional[str] = None):
        '''
        Broadcast messages through websocket
        
        Parameters:
            message (str): The message to broadcast.
            client_type: [Optional](str): The client type to send message to. Sends to all if none
            session_id: [Optional](str): The session ID to send message to. Sends to all sessions if none.
        '''
        if session_id:
            print(f"trying to broadcast to {session_id}")
            # Broadcast to a specific session
            #print(self.session_connections)
            if session_id in self.session_connections:
                print(f"{session_id} is in self.session_connections!")
                if client_type:
                    print(self.session_connections)
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
        '''

        '''
        if session_id:
            return len(self.session_connections.get(session_id, {}).get(client_type, []))
        else:
            return len(self.general_connections.get(client_type, []))

    async def trySendMessage(self, connection: WebSocket, message: str):
        if not connection.client_state == WebSocketState.CONNECTED:
            print("websocket not connected")
            return
        try:
            await connection.send_text(message)
        except RuntimeError as e:
            print(f"Error sending message: {e}")

    def find_websocket_index(self, client_type: str, websocket: WebSocket) -> int: #????
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
                            print(f"'{str(sessionID)}'")
                            for session in manager.session_connections:
                                print("session")
                                print(f"'{session}'")
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
        await manager.broadcast(f"Web-apps connected: {manager.getNrOfClients('web')}, Cameras connected: {manager.getNrOfClients('mobile')}")


'''
SESSION WEBSOCKET
'''
@app.websocket("/ws/{session_id}/session")
async def websocket_endpoint(websocket: WebSocket, session_id: str, client_type: str):
    activeSession = sessionManager.findSessionByID(session_id)
    await manager.connect(websocket, client_type, session_id=session_id)
    print(f"BROADCASTING: Session {session_id} mobiles connected: {manager.getNrOfClients(client_type='mobile', session_id=session_id)}")
    await manager.broadcast(f"Session {session_id} mobiles connected: {manager.getNrOfClients(client_type='mobile', session_id=session_id)}", session_id=session_id)
    try:
        while True:
            
            data = await websocket.receive()
            #print(f"received message in {session_id}")
            #print(f"data.type is: {data["type"]}")
            if data["type"] == "websocket.disconnect":
                break

            if data["type"] == "websocket.receive":
                if "text" in data:
                    message = data["text"]
                    #print(data)
                    #print(len(session_id))
                    if client_type == "web":
                        # Message to create new Session.
                        if message =="newSession":
                            # Create new session
                            print("creating new session")
                            sessionManager.addSession(Session())
                            sessionID = sessionManager.activeSession.getID()
                            await manager.send_personal_message(f"New session id: {sessionID} ", websocket)
                        else: # handle as JSON.
                            message = json.loads(data['text'])
                            # Access the fields from the message
                            session_id_msg = message.get('session') #Can double check that this matches with session_id
                            command = message.get('command')
                            if command == "start_calibration":
                                rows = int(message.get('rows'))
                                print(f"rows is of type: {type(rows)}")
                                cols = int(message.get('cols'))
                                print(f"cols is of type: {type(cols)}")

                                square_size = float(message.get('squareSize'))
                                placement = message.get('placement')  # Assuming this is a string

                                # Send parameters to session
                                activeSession.set_checkerboard_params(rows, cols, square_size, placement)
                                
                                # Start the calibration on the back end...
                                #For now just set the checkerboard_params and notify webapp.
                                print(f"received start_calibration")
                                print(f"session ID match: {session_id_msg==session_id}")
                                print(f"session_id is of type: {type(session_id)}")
                                await sessionManager.startTrial(session= activeSession, trialType = "calibration", process = False)
                                #await manager.broadcast(f"Toast: Info: {sessionManager.activeSession.checkerBoard}", client_type="web", session_id=session_id)


                            


                            #print(f"Session {session_id} says: {message}")
                        #await manager.broadcast(f"Session {session_id} says: {message}", "mobile", session_id=session_id)

                    else: #Client_type is mobile.
                        message = json.loads(data['text'])
                        command = message.get('command')

                        if command == "mobile_connected": #New camera connected to session.
                                #Add the content to session camera information.
                                if activeSession:
                                    # Get camera model from message
                                    cameraModel = str(message.get("content"))
                                    print(f"camera model is: {cameraModel}")
                                    #add the camera model to the session
                                    activeSession.iphoneModel[f"cam{manager.find_websocket_index(client_type,websocket)}"] = cameraModel
                        
                        if command == "save_video": # A mobile sent a video to session.
                            # Extract metadata and Base64-encoded video data
                            metadata = message.get("metadata", {})
                            base64_data = message.get("videoData", "")
                            name = metadata.get("name")
                            # Decode the Base64 string back to binary data
                            video_data = base64.b64decode(base64_data)

                            # Save the video to a file
                            save_binary_file(video_data, f"{name}cam{manager.find_websocket_index(client_type, websocket)}.mov")
                            
                        #await manager.broadcast(f"Session {session_id} received a message it cant deal with right now", "web", session_id=session_id)
                        #await manager.broadcast(f"Session {session_id} Mobile says: {message}", "web", session_id=session_id)

                elif "bytes" in data: #Should only be movies for now, so only from mobile/camera clients.
                    binary_data = data["bytes"]
                    # Handle binary data here
                    print(f"Received binary data: {len(binary_data)} bytes")
                    # You could save the binary data to a file, process it, etc.
                    binary_data = data["bytes"]
                    # Save binary data to a file
                    # TODO: Make a filemanager for this
                    save_binary_file(binary_data, f"received_file_cam{manager.find_websocket_index(client_type,websocket)}.mov")
                    # Optionally broadcast the receipt
                    await manager.broadcast(f"Received binary data of size: {len(binary_data)} bytes", session_id=session_id)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, client_type, session_id=session_id)
        logger.debug("A client is disconnecting")
        await manager.broadcast(f"Session {session_id} Web-apps connected: {manager.getNrOfClients('web')}, Cameras connected: {manager.getNrOfClients('mobile')}", session_id=session_id)
import os

def save_binary_file(data: bytes, filename: str):
    os.listdir()
    with open(filename, 'wb') as file:
        file.write(data)
        file.close()
    print(f"File saved as {filename}")

    # Check if the file was successfully saved
    if os.path.isfile(filename):  # Check if the file exists
        # Optionally check the file size
        if os.path.getsize(filename) > 0:  # Check if the file is not empty
            print(f"File saved successfully as {filename}")
        else:
            print(f"File saved as {filename} but it is empty.")
    else:
        print(f"Failed to save the file as {filename}.")

if __name__=="__main__":
    hostname = socket.gethostname()    
    print(f"Hostname: {hostname}")

    #ip_address = socket.gethostbyname(hostname) #"192.168.0.48"#socket.gethostbyname(hostname)
    print(f"IP Address: {ip_address}")
    ip_address = "0.0.0.0" # debug
    print(f"IP Address: {ip_address}")

    uvicorn.run(app,host=ip_address,port=8080)