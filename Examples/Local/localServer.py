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
from FileManager import FileManager
import os
import pickle 
import threading
import time
import asyncio
from localReprocess import runLocalTrial

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

    def saveSubject(self, subject: Subject):
        loaded_subjects = fileManager.load_subjects()
        loaded_subjects.append(subject)
        fileManager.save_subjects(loaded_subjects)
    
    def removeSubject(self, subject: Subject):
        loaded_subjects = fileManager.load_subjects()
        loaded_subjects.remove(subject)
        fileManager.save_subjects(loaded_subjects)

    # Should do this a better way maybe
    def findSessionByID(self, session_id: str) -> Optional[Session]:
        # Check activate connections
        for session in self.sessions:
            print("checking active sessions...")
            if str(session.getID()) == session_id:
                return session
        #Otherwise check old sessions
        saved_sessions = fileManager.find_sessions()
        print("checking saved sessions:")
        for session_name, session_info in saved_sessions.items():
            print(session_name)
            if session_id == session_name:
                return Session(session_uuid=session_id)
        return None
    
    async def sendStartTrial(self, websocket: WebSocket, session_id: str, trialType: Optional[str] = "dynamic"):
        message = {
            "command": "start",
            "trialType": trialType,
            "content": '',
            "session_id": session_id
            }
        json_message = json.dumps(message)
        await manager.broadcast(message=json_message, source= websocket)
    
    async def sendStopTrial(self, websocket: WebSocket):
        message = {
            "command": "stop",
            "content": '',
            "trialType": '',
            "session_id": ''
        }
        json_message = json.dumps(message)
        await manager.broadcast(message = json_message, source = websocket)
    
    async def startTrial(self, websocket: WebSocket, session: Session, trialType: Optional[str] = "dynamic", process=True, isTest=False,  trialNames: Optional[str] = ""):
        '''
        Creates and starts a new trial within the given session.

        The function initiates the trial by:
            - Commanding all mobile devices in the session to begin recording.
            - Automatically stopping recordings after 1 second if the trial type is 'static' or 'calibration'.
            - Saving the recorded videos.
            - If 'process' is True, the function sends a request to the regular opencap-core main function to process the videos.

        Parameters:
            websocket: (WebSocket): The websocket to communicate through.
            session (Session): The session in which the trial is being conducted.
            trialType (Optional[str]): The type of trial to start ('calibration', 'static', 'dynamic'). Defaults to 'dynamic'.
            process (bool): Whether to process the trial immediately after recording. Defaults to True.
            isTest (bool): Whether to use a preset test trial instead of the actual session provided. Defaults to False.
            trialName (Optional[str]): An optional name for the trial. Defaults to an empty string.

        Returns:
            dict: Information about whether the trial was successfully processed and/or uploaded.
        '''
        print(f"running {trialType} trial")
        session_id = str(session.getID())
        try:
            #Start recording
            
            await self.sendStartTrial(websocket=websocket, session_id = session_id, trialType=trialType)
            if trialType == 'calibration' or trialType == 'neutral':
                toastMsg = {
                    "command": "Toast",
                    "type": "Info",
                    "content": "Recording {trialType}"
                }
                await manager.send_personal_message(json.dumps(toastMsg), websocket = websocket)
                # Stop recording automatically after 1 second.
                await asyncio.sleep(1)
                await self.sendStopTrial(websocket=websocket)
                # TODO: Add check that the files are correctly saved.
                toastMsg = {
                    "command": "Toast",
                    "type": "Success",
                    "content": "succesfully finished recording {trialType}"
                }
                await manager.send_personal_message(json.dumps(toastMsg), websocket=websocket)
            elif trialType=='dynamic':
                print("Trial Type is dynamic")
                if not isTest:
                    # TODO: Wait to ensure that all files are uploaded before proceeding
                    # TODO: ... Should probably do that for calib and neutral too.
                    print("this is a real trial recording")

            #Upload files
            if process:
                sessionId = str(session.getID())

                #If isTest then we just use a pre recorded session.
                if isTest:
                    sessionId = "Giota"

                    # Set trialNames based on the trialType
                    trialNames = (
                        trialType 
                        if (trialType == "calibration" or trialType == "neutral") 
                        else "dynamic_2"
                    )
                    # Set trialId based on the trialType
                    trialId = "Dynamic_1" if trialType == "calibration" else "Calib_1" if trialType == "neutral" else "Dynamic_2" if trialType == "dynamic" else None

                runLocalTrial(sessionId, trialNames, trialId, trialType=trialType, dataDir=fileManager.base_directory)
                
                #raise CustomError("Process not implemented yet")
                #Process files

        except CustomError as e:
            toastMsg = {
                    "command": "Toast",
                    "type": "Error",
                    "content": "error: {e}"
                }
            await manager.send_personal_message(message=json.dumps(toastMsg), websocket=websocket)
        else:
            #Successfully processed trial
            toastMsg = {
                    "command": "Toast",
                    "type": "Success",
                    "content": "success: succesfully processed {trialType}"
                }
            await manager.send_personal_message(message=json.dumps(toastMsg), websocket=websocket)

            succesCalibrationMsg = {
                "command": "calibration",
                "content": "success",
                "session": session_id
            }
            await manager.send_personal_message(message=json.dumps(succesCalibrationMsg), websocket=websocket)
        return

class ConnectionManager:
    def __init__(self):
        # Dictionary to store connections
        # Each web connection can have a list of linked mobile connections
        self.connections: Dict[WebSocket, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_type: str, link_to_web: Optional[WebSocket] = None):
        """
        Connect a websocket and optionally link it to an existing web connection.

        Args:
            websocket (WebSocket): The websocket connection to be added.
            client_type (str): Type of the client ('web' or 'mobile').
            link_to_web (Optional[WebSocket]): The web connection to which this mobile connection should be linked.
        """
        await websocket.accept()
        if client_type == "web":
            if websocket not in self.connections:
                self.connections[websocket] = []  # Initialize an empty list for linked mobiles
        elif client_type == "mobile" and link_to_web:
            if link_to_web in self.connections:
                self.connections[link_to_web].append(websocket)
            else:
                raise ValueError("Specified web connection does not exist to link the mobile connection.")
        else:
            raise ValueError("Invalid client type or missing web link for mobile connection.")

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a websocket and clean up any references.

        Args:
            websocket (WebSocket): The websocket connection to be removed.
        """
        # If it's a web connection, remove all linked mobiles
        if websocket in self.connections:
            linked_mobiles = self.connections.pop(websocket)
            for mobile in linked_mobiles:
                try:
                    mobile.close()
                except Exception as e:
                    print(f"Error closing mobile connection: {e}")
        else:
            # If it's a mobile connection, remove it from any linked web connections
            for web_connection, linked_mobiles in self.connections.items():
                if websocket in linked_mobiles:
                    linked_mobiles.remove(websocket)
                    break

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a personal message to a specific websocket.

        Args:
            message (str): The message to send.
            websocket (WebSocket): The websocket to send the message to.
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(message)
            except RuntimeError as e:
                print(f"Error sending message: {e}")
        else:
            print("WebSocket is not connected.")

    async def broadcast(self, message: str, source: WebSocket):
        """
        Broadcast a message from a source websocket to its linked connections.

        Args:
            message (str): The message to broadcast.
            source (WebSocket): The source websocket (either web or mobile). If this is a web connection it will send to linked mobiles. A mobile connection will send only to the linked web connection.

        """
        if source in self.connections:
            # Broadcast from web to all linked mobiles
            for mobile in self.connections[source]:
                await self.try_send_message(mobile, message)
        else:
            # Broadcast from mobile to its linked web connection
            for web_connection, linked_mobiles in self.connections.items():
                if source in linked_mobiles:
                    await self.try_send_message(web_connection, message)
                    break

    def get_nr_of_clients(self, client_type: str) -> int:
        """
        Get the number of connected clients of a specific type.

        Args:
            client_type (str): The type of clients to count ('web' or 'mobile').

        Returns:
            int: The number of connected clients.
        """
        if client_type == "web":
            return len(self.connections)
        elif client_type == "mobile":
            return sum(len(mobiles) for mobiles in self.connections.values())
        else:
            raise ValueError("Invalid client type. Must be 'web' or 'mobile'.")

    def find_websocket_index(self, websocket: WebSocket) -> int:
        """
        Find the index of a mobile websocket in its linked web connection.

        Args:
            websocket (WebSocket): The mobile websocket to locate.

        Returns:
            int: The index of the mobile websocket within its linked web connection's list of connections.
                 Returns -1 if the websocket is not linked to any web connection.
        """
        for web_connection, linked_mobiles in self.connections.items():
            if websocket in linked_mobiles:
                return linked_mobiles.index(websocket)
        return -1  # Not found

    async def try_send_message(self, connection: WebSocket, message: str):
        """
        Try to send a message to a websocket connection.

        Args:
            connection (WebSocket): The websocket connection.
            message (str): The message to send.
        """
        if connection.client_state == WebSocketState.CONNECTED:
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"Error sending message: {e}")
        else:
            print("WebSocket is not connected.")

    async def announce(self, message:str):
        '''
        Send message to all web connections

        Args:
            message (str): The message to send.
        '''        
        for web_connection, mobil_connection in self.connections.items:
            await self.try_send_message(message=message, connection=web_connection)

        
'''sync def broadcast(self, message: str, client_type: str):
        for connection in self.active_connections[client_type]:
            if not connection.client_state == WebSocketState.CONNECTED:
                continue
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"Error sending message: {e}")'''
        


manager = ConnectionManager()
## TODO: Get this base filepath to work correctly. Should be in Examples/data but not
# § /Examples/Local/Examples/data like it is now.. seems to work
current_script_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.abspath(os.path.join(current_script_directory, '..'))
base_directory = os.path.join(parent_directory, 'Data')

fileManager = FileManager(base_directory)
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
    logger.debug(f"Clients connected: {manager.get_nr_of_clients(client_type)}")

    #await manager.broadcast(
    #    f"General Web-apps connected: {manager.getNrOfClients('web')}\n"
    #    f"General Cameras connected: {manager.getNrOfClients('mobile')}",
    #    client_type
    #)

    try:
        while True:
            data = await websocket.receive()
            if data["type"] == "websocket.disconnect":
                break

            if data["type"] == "websocket.receive":
                if "text" in data:
                    message = data["text"]
                    print(f"message received is: {message}")
                    # Parse JSON message
                    try:
                        message_json = json.loads(message)
                    except json.JSONDecodeError:
                        await manager.send_personal_message("Error: You sent a Invalid JSON format.", websocket)
                        continue

                    command = message_json.get("command")
                    session_id = message_json.get("session")  # Optional session key

                    # Determine the session if applicable
                    active_session = None
                    if session_id:
                        active_session = sessionManager.findSessionByID(session_id)
                        if not active_session:
                            await manager.send_personal_message(
                                f"Error: No session found with ID {session_id}", websocket
                            )
                            continue

                    # Route the message
                    if client_type == "web":
                        await handle_web_message(
                            websocket, message_json, command, active_session, session_id
                        )
                    else:
                        await handle_mobile_message(
                            websocket, message_json, command, active_session, session_id
                        )

                elif "bytes" in data:
                    binary_data = data["bytes"]
                    print(f"Received binary data: {len(binary_data)} bytes")
                    save_binary_file(
                        binary_data,
                        f"received_file_cam{manager.find_websocket_index(client_type, websocket)}.mov"
                    )
                    await manager.broadcast(
                        f"Received binary data of size: {len(binary_data)} bytes",
                        session_id=session_id if session_id else None
                    )

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
        logger.debug("A client is disconnecting")
       

async def handle_web_message(websocket, message_json, command, active_session: Session, session_id):
    print(f"Received command: {command}")
    
    if active_session:
        # Handle session-specific commands
        if command == "start_calibration":
            rows = int(message_json.get("rows"))
            cols = int(message_json.get("cols"))
            square_size = float(message_json.get("squareSize"))
            placement = message_json.get("placement")
            is_test = message_json.get("isTest")

            active_session.set_checkerboard_params(rows, cols, square_size, placement)
            fileManager.save_session_metadata(active_session)
            await sessionManager.startTrial( websocket=websocket,
                session=active_session, trialType="calibration", process=True, isTest=is_test
            )

        elif command == "start_neutral":
            is_test = message_json.get("isTest")
            subject = Subject.from_dict(message_json.get("subject"))
            active_session.set_subject(subject)
            fileManager.save_session_metadata(active_session)
            await sessionManager.startTrial( websocket=websocket,
                session=active_session, trialType="neutral", process=True, isTest=is_test
            )
        elif command == "start_dynamic":
            is_test = message_json.get("isTest")
            trialName = message_json.get("trialName")       

            await sessionManager.startTrial( websocket=websocket,
                 session = active_session, trialType="dynamic", process = True, isTest=is_test, trialNames=trialName)                          

        elif command == "get_session_trials":
            isTest = message_json.get("isTest")
            if isTest:
                trials = fileManager.find_trials(session=Session(session_uuid="Giota"))
            else:
                trials = fileManager.find_trials(session=active_session)
            jsonMsg = {
                "command": "sessionTrials",
                "content": trials,
                "session": active_session.uuid
            }
            await manager.send_personal_message(message=json.dumps(jsonMsg), websocket=websocket)

        elif command == "get_visualizer":
            trialName = message_json.get("trialName")
            visualizerJson = fileManager.find_visualizer_json(session=active_session, trialName=trialName)
            jsonMsg = {
                "command": "visualizerJSON",
                "content": visualizerJson,
                "session": active_session.uuid
            }
            await manager.send_personal_message(message=json.dumps(jsonMsg), websocket=websocket)
        else:
            toastMsg = {
                "command": "Toast",
                "type": "Error",
                "message": "Error: Unknown session-specific command '{command}"
            }
            await manager.send_personal_message(
                json.dumps(toastMsg), websocket
            )
    else:
        if command == "newSession":
            sessionManager.addSession(Session())
            session_id = sessionManager.activeSession.getID()
            fileManager.create_session_directory(sessionManager.activeSession)
            newSessionMsg = {
                "command": "new_session",
                "content": session_id
            }
            await manager.send_personal_message(json.dumps(newSessionMsg), websocket)

        elif command == "get_subjects":
            loaded_subjects = [subject.to_dict() for subject in fileManager.load_subjects()]
            response = {"command": "subjects", "content": loaded_subjects}
            await manager.send_personal_message(json.dumps(response), websocket)

        elif command == "get_sessions":
            sessions = fileManager.find_sessions()

            response = {"command": "sessions", "content": sessions}
            print(response)
            await manager.send_personal_message(json.dumps(response), websocket)

        elif command == "ping":
            pongMsg = {
                command: "pong"
            }
            await manager.send_personal_message(json.dumps(pongMsg), websocket=websocket)
            # General commands that require session_id

           # await manager.send_personal_message(
            #    f"Error: Command '{command}' requires a session ID", websocket
            #)

async def handle_mobile_message(websocket, message_json, command, active_session: Session, session_id):
    if command == "mobile_connected" and active_session:
        camera_model = str(message_json.get("content"))
        camera_index = manager.find_websocket_index('mobile', websocket)
        active_session.iphoneModel[f"cam{manager.find_websocket_index('mobile', websocket)}"] = camera_model
        message = {
            "command": "mobile_connected",
            "content": camera_index,
            "session_id": session_id
            }
        json_message = json.dumps(message)
        manager.broadcast(json_message, websocket)

    elif command == "save_video" and active_session:
        metadata = message_json.get("metadata", {})
        base64_data = message_json.get("videoData", "")
        trial_name = metadata.get("name")
        trial = active_session.get_trial_by_name(trial_name)

        video_data = base64.b64decode(base64_data)
        fileManager.save_binary_file(
            video_data, session=active_session, trial=trial, cam_index=manager.find_websocket_index('mobile', websocket)
        )

    elif not active_session:
        await manager.send_personal_message(
            f"Error: Command '{command}' requires a session ID", websocket
        )
    else:
        await manager.send_personal_message(
            f"Error: Unknown command '{command}'", websocket
        )

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
    subjects = [
    Subject(name="John Doe", sex="m", height=1.75, weight=70),
    Subject(name="Jane Doe", sex="f", height=1.65, weight=60),
    Subject(name="Alex Doe", sex="o", height=1.8, weight=75)
]

    # Save the list of subjects to a file
    with open("subjects_data.pkl", 'wb') as file:
        pickle.dump(subjects, file)

    # Load the list of subjects from the file
    with open("subjects_data.pkl", 'rb') as file:
        loaded_subjects = pickle.load(file)

    # Example: Print details of loaded subjects
    for subject in loaded_subjects:
        print(f"Name: {subject.name}, Gender: {subject.gender}, Height: {subject.height}, Weight: {subject.mass}, id: {subject.id}")
    hostname = socket.gethostname()
    print(os.listdir())
    print(f"Hostname: {hostname}")

    #ip_address = socket.gethostbyname(hostname) #"192.168.0.48"#socket.gethostbyname(hostname)
    #ip_address = "192.168.0.48"
    ip_address = "130.229.141.43" # ubuntu computer
    #ip_address = "192.168.50.9" Landet
    print(f"IP Address: {ip_address}")

    uvicorn.run(app,
                host=ip_address,
                port=8080
                #ssl_certfile="cert.pem",
                #ssl_keyfile="key.pem"
                )