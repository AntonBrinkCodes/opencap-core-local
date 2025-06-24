from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, UploadFile, Request
from fastapi.websockets import WebSocketState
from mangum import Mangum
import uvicorn
from typing import List, Dict, Optional
import logging
from sessionModel import Session, Trial, Subject
import json
import base64
from FileManager import FileManager
import os
import pickle 
import threading
from datetime import datetime
import asyncio
from localReprocess import runLocalTrial
from fastapi.responses import FileResponse


from enum import Enum # Maybe or something else

app = FastAPI()
handler = Mangum(app)

import socket


                
                
class CustomError(Exception):
    pass

class ProcessTrial:
    """
    Represents a trial within a session, including metadata and websocket connection.

    Attributes:
        session (Session): The session this trial belongs to.
        websocket (WebSocket): WebSocket for communication during the trial.
        trialId (str): Unique identifier for the trial.
        trialType (str): Type of the trial (e.g., "dynamic", "neutral").
        trialName (str): A descriptive name for the trial.
        timeAdded (datetime): Timestamp when the trial was created.
    """

    def __init__(
        self,
        session: Session,
        websocket: WebSocket,
        trialId: str,
        trialType: str = "dynamic",
        trialName: str = "burpees",
        timeAdded: datetime = None,
        isTest: bool = False,
        forceRedoPoseEstimation: bool = False,
        poseDetector = "hrnet",
        cameras_to_use = ["all"]
    ):
        """
        Initializes a new instance of the ProcessTrial class.

        Args:
            session (Session): The session the trial belongs to.
            websocket (WebSocket): The websocket to communicate with.
            trialId (str): Unique ID of the trial.
            trialType (str, optional): Type of trial. Defaults to "dynamic".
            trialName (str, optional): Human-readable trial name. Defaults to "burpees".
            timeAdded (datetime, optional): Time the trial was added. Defaults to now if not provided.
            isTest (Bool, optional): If the trial is just a test trial.
        """
        self.session = session
        self.websocket = websocket
        self.trialId = trialId
        self.trialType = trialType
        self.trialName = trialName
        self.timeAdded = timeAdded or datetime.now()
        self.isTest = isTest,
        self.forceRedoPoseEstimation = forceRedoPoseEstimation,
        self.poseDetector = poseDetector,
        self.cameras_to_use = cameras_to_use

class sessionManager:
    def __init__(self):
        self.sessions: List[Session] = []
        self.activeSession: Optional[Session] = None
        self.isProcessing = False
        self.processingTrials = {} # Dict with key: uuid as a string, and values are either: 'processing' or 'queued'. Info in this is shared to webapp.
        self.processQueue = {} # Dict for queueing the processing trials. 

    #Checks the processQueue for the next trial to run.
    #Should prioritize Neutral if they exist
    def checkQueue(self) -> Optional[ProcessTrial]:
        print("Checking queue...")
        return self.get_oldest_trial(self.processQueue)
    
    def get_oldest_trial(self, trials: dict) -> Optional[ProcessTrial]:
        if not trials:
            return None

        neutral_trials = [t for t in trials.values() if t.trialType == "neutral"]

        if neutral_trials:
            # Return the neutral trial with the oldest timeAdded
            return min(neutral_trials, key=lambda t: t.timeAdded)

        # Otherwise return the oldest overall
        return min(trials.values(), key=lambda t: t.timeAdded)


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

    def get_trials(self, session: Session):
        # Get the trials saved to files
        trials = fileManager.find_trials(session=session)
        print(self.processingTrials)
        for key, subdict in trials.items():
            print(subdict.get("uuid"))
            if subdict.get("uuid") in self.processingTrials:
                #print("found uuid match in giota!")
                subdict["processed"] = self.processingTrials[subdict["uuid"]]
        
        print(trials)
        return trials

    # Should do this a better way maybe
    def findSessionByID(self, session_id: str) -> Optional[Session]:
        # Check activate connections
        for session in self.sessions:
            print("checking active sessions...")
            if str(session.getID()) == session_id:
                return session
        #Otherwise check old sessions
        saved_sessions = fileManager.load_sessions()
        print("checking saved sessions:")
        for session_name, session_info in saved_sessions.items():
            print(session_name)
            if session_id == session_name:
                return session_info
        return None
    
    async def sendUpdatedTrials(self, websocket: WebSocket, session_id: str):
        trials = self.get_trials(session=Session(session_uuid=session_id))
        # Prepare and send JSON message
        jsonMsg = {
            "command": "sessionTrials",
            "content": trials,
            "session": session_id
        }
        await manager.send_personal_message(json.dumps(jsonMsg), websocket)
    
    async def sendStartTrial(self, websocket: WebSocket, session_id: str, trialType: Optional[str] = "dynamic"):
        message = {
            "command": "start",
            "trialType": trialType,
            "content": '',
            "session": session_id
            }
        json_message = json.dumps(message)
        await manager.broadcast(message=json_message, source= websocket)
    
    async def sendStopTrial(self, websocket: WebSocket, session_id :str, trialName: str, trialId: str, trialType: str):
        message = {
            "command": "stop",
            "trialId": trialId,
            "trialName": trialName,
            "content": '',
            "trialType": trialType,
            "session": session_id
        }
        json_message = json.dumps(message)
        await manager.broadcast(message = json_message, source = websocket)

    async def startRecording(self, websocket: WebSocket, session: Session, trialId: str, trialType: str = "dynamic", trialName: Optional[str] = "defaultName"):
        '''
        Sends messages to the connected mobile websockets to start recording.

        Args:
            session (Session): The corresponding recording Session.
            trialId (str): the trialId of the recording/trial.
            trialType (str): dynamic, neutral or calibration.
            trialName: (str): Optional. Only required for dynamic trials (TODO: Implement this...)

        '''
        session_id = str(session.getID())
        try:
            #Start recording
            
            await self.sendStartTrial(websocket=websocket, session_id = session_id, trialType=trialType)
            if trialType == 'calibration' or trialType == 'neutral':
                toastMsg = {
                    "command": "Toast",
                    "type": "Info",
                    "content": f"Recording {trialType}"
                }
                await manager.send_personal_message(json.dumps(toastMsg), websocket = websocket)
                # Stop recording automatically after 1.5 second.
                await asyncio.sleep(1.5)
                await self.sendStopTrial(websocket=websocket, session_id=session_id, trialName=trialName, trialId=trialId, trialType=trialType)
                if trialType == 'neutral':
                    toastMsg = {
                        "command": "Toast",
                        "type": "Info",
                        "content": f"Finished recording. Subject can relax"
                    }
                    await manager.send_personal_message(json.dumps(toastMsg), websocket=websocket)
            
            else: #If dynamic, just send to start and the user sends to stop through web app.

                toastMsg = {
                    "command": "Toast",
                    "type": "Info",
                    "content": f"Recording {trialType}"
                }
                await manager.send_personal_message(json.dumps(toastMsg), websocket = websocket)

        except CustomError as e:
            toastMsg = {
                    "command": "Toast",
                    "type": "Error",
                    "content": "error: {e}"
                }
            await manager.send_personal_message(message=json.dumps(toastMsg), websocket=websocket)

    async def wait_for_gpu(self, interval=20):
        """
        Wait until the computer is no longer processing a trial

        Args:
            interval (int): How often to check (in seconds).

        Returns:
            int: The ID of the GPU that meets the criteria.
        """
        while self.isProcessing:
            await asyncio.sleep(interval)
    
    async def processTrial(self, websocket: WebSocket, session: Session, trialId: str, trialType: Optional[str] = "dynamic", isTest=False,  trialNames: Optional[str] = "", cameras_to_use: [str] = ["all"], poseDetector = "hrnet"):
        """
        Process a trial based on the given session, trial type, and testing flag.

        Args:
            session: The session object containing session information.
            trialType (str): The type of trial (e.g., "calibration", "neutral", "dynamic").
            isTest (bool): Whether the process is a test or not.
            fileManager: The file manager instance to handle file-related operations.
            manager: The manager instance for handling WebSocket communication.
            websocket: The WebSocket connection for sending messages.

        Returns:
            None
        """
        # Initialize session ID
        sessionId = str(session.getID())

        # If isTest, use pre-recorded session data
        if isTest:
            sessionId = "Giota"

            # Set trialNames based on the trialType
            trialNames = (
                trialType
                if trialType in {"calibration", "neutral"}
                else "dynamic_2"
            )

            # Set trialId based on the trialType
            trialId = (
                "Dynamic_1" if trialType == "calibration" else
                "Calib_1" if trialType == "neutral" else
                "Dynamic_2" if trialType == "dynamic" else
                None
            )

        # Run the trial locally TODO: Add some kind of check here or maybe a "try" to prevent crashes :)
        res = None
        
        if trialType != "calibration": #GPU only neededd for dynamic and neutral trials.
            print("Checking for available GPU")
            if trialId in self.processQueue.keys():
                print(f"Processing {trialNames} from queue")
            else: 
                self.processQueue[trialId] = ProcessTrial(websocket = websocket, session = session, trialId = trialId, trialName = trialNames, trialType = trialType, poseDetector=poseDetector, cameras_to_use=cameras_to_use) # Add to queue
            if trialType == "dynamic":
                self.processingTrials[trialId] = "queued"
                await self.sendUpdatedTrials(websocket=websocket, session_id=sessionId)
            
            if self.isProcessing: # Already added trial to processQueue and sent the information to web server
                return
            
        print(f"processing trial: {trialNames}, with id: {trialId}. Type: {trialType}")
        self.isProcessing = True
        try:
            if trialType == "dynamic":
                self.processingTrials[trialId] = "processing"
                await self.sendUpdatedTrials(websocket=websocket, session_id=sessionId)
            print(f"cameras to use is: {cameras_to_use}")
            res = await asyncio.to_thread(runLocalTrial, sessionId, trialNames, trialId, trialType=trialType, dataDir=fileManager.base_directory)
            if res!=None:
                print("Succesfully processed trial")
                successMsg = {
                    "command": "process_succeded",
                    "trialType": trialType,
                    "trialId": trialId,
                    "session": sessionId
                }
                await manager.send_personal_message(json.dumps(successMsg), websocket)
                # Handle "dynamic" trial type
                if trialType == "dynamic":
                    self.processingTrials.pop(trialId)
                    await self.sendUpdatedTrials(websocket=websocket, session_id=sessionId)
        except Exception as inst:
            print(f"Error: {type(inst)}! Args: {inst.args} ")
            self.processingTrials[trialId] = "Error"
            if trialType == "dynamic":
                await self.sendUpdatedTrials(websocket=websocket, session_id=sessionId)
            if trialType == "neutral":
                self.processingTrials.pop(trialId)
            print(inst)
            toastMsg = {
                "command": "Toast",
                "type": "Error",
                "content": f"Error from server: {inst}"
            }
            await manager.send_personal_message(json.dumps(toastMsg), websocket)
        finally:
            self.isProcessing = False
            if trialType != "calibration":
                self.processQueue.pop(trialId) # Remove from queue
            nextTrial = self.checkQueue()
            print(f"next trial is: {nextTrial} and is type: {type(nextTrial)}")
            if nextTrial != None:
                self.processTrial(websocket=nextTrial.websocket, session=nextTrial.session, trialId= nextTrial.trialId,
                                 trialType=nextTrial.trialType, trialNames = nextTrial.trialName, isTest=nextTrial.isTest, cameras_to_use=cameras_to_use, poseDetector=poseDetector)

    
class ConnectionInfo:
    """
    Represents the information associated with a web connection.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id  # The session ID for the web connection
        self.mobiles: List[WebSocket] = []  # List of linked mobile connections

    def __str__(self):
        """
        Return a string representation of the ConnectionInfo instance.
        """
        return f"Session ID: {self.session_id}, Linked Mobile Connections: {len(self.mobiles)}"
    
    def __iter__(self):
        """
        Allow iteration over the list of linked mobile connections.
        """
        return iter(self.mobiles)

class ConnectionManager:
    def __init__(self):
        # Dictionary to store connections
        # Each web connection can have a list of linked mobile connections
        self.connections: Dict[WebSocket, ConnectionInfo] = {}

    async def connect(self, websocket: WebSocket, client_type: str, session_id: Optional[str] = None):
        """
        Connect a new WebSocket. Associate session IDs for web clients and link mobile clients.

        Args:
            websocket (WebSocket): The WebSocket connection to add.
            client_type (str): Either "web" or "mobile".
            session_id (Optional[str]): The session ID for the web client.
        """
        await websocket.accept()

        if client_type == "web":
            # Add a web client with session ID and an empty list of mobiles
            if websocket not in self.connections:
                self.connections[websocket] = ConnectionInfo(session_id=session_id or "")
            else:
                raise ValueError("Web connection already exists.")
        elif client_type == "mobile":
            if session_id:
                # Find the web client with the given session ID
                web_client = self.find_web_connection_by_id(session_id)
                if web_client:
                    # Append the mobile connection to the linked web client
                    self.connections[web_client].mobiles.append(websocket)
                else:
                    raise ValueError("Web client with the given session ID not found.")
            else:
                raise ValueError("Missing session ID for mobile connection.")
        else:
            raise ValueError("Invalid client type.")

    def find_web_connection_by_id(self, session_id: str) -> Optional[WebSocket]:
        """
        Find a web client WebSocket by its session ID.

        Args:
            session_id (str): The session ID to search for.

        Returns:
            Optional[WebSocket]: The corresponding WebSocket if found, or None.
        """
        for web_socket, connection_info in self.connections.items():
            
            if str(connection_info.session_id) == session_id:
                return web_socket
        return None

    def update_session_id(self, websocket: WebSocket, new_session_id: str):
        """
        Update the session ID for a given web client.

        Args:
            websocket (WebSocket): The WebSocket connection to update.
            new_session_id (str): The new session ID.
        """
        if websocket in self.connections:
            self.connections[websocket].session_id = new_session_id
        else:
            raise ValueError("WebSocket connection not found.")

    def get_session_mobiles(self, session_id: str) -> Optional[List[WebSocket]]:
        """
        Get all mobile WebSockets linked to a specific session ID.

        Args:
            session_id (str): The session ID of the web client.

        Returns:
            Optional[List[WebSocket]]: The list of mobile WebSockets, or None if session not found.
        """
        web_client = self.find_web_connection_by_id(session_id)
        if web_client:
            return self.connections[web_client].mobiles  # Return the list of mobiles
        return None

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket to remove.
        """
        # If the WebSocket is a web client, remove it and its associated mobiles
        if websocket in self.connections:
            del self.connections[websocket]
        else:
            # If it's a mobile client, remove it from the linked mobiles list
            for web_socket, connection_info in self.connections.items():
                if websocket in connection_info.mobiles:
                    connection_info.mobiles.remove(websocket)
                    break

    def disconnect_mobiles(self, websocket: WebSocket):
        # Check if the websocket is a web connection in the connections dictionary
        if websocket in self.connections:
            # Get the ConnectionInfo for the given web connection
            connection_info = self.connections[websocket]

            # Iterate over the mobiles associated with this connection
            for mobilesocket in connection_info.mobiles:
                self.disconnect(mobilesocket)  # Disconnect each mobile websocket

            #  clear the list of mobiles
            connection_info.mobiles.clear()

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
            return len(self.connections) # Count of web connections
        elif client_type == "mobile":
            return sum(len(info.mobiles) for info in self.connections.values())  # Count of mobile clients

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
        for web_socket, info in self.connections.items():
            if websocket in info.mobiles:
                return info.mobiles.index(websocket)  # Get the index of the mobile websocket
        return -1  # Return -1 if the websocket is not found

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
        for web_connection, mobile_connection in self.connections.items:
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

@app.get("/download/{file_name}")
async def download_file(file_name: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(fileManager.base_directory, file_name)
    
    # Check if the file exists
    if os.path.exists(file_path):
        # Add a background task to delete the file after the response is sent
        background_tasks.add_task(fileManager.removePath, file_path)
        
        # Return the file as a response, setting the filename for the download prompt
        return FileResponse(
            file_path,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
            background=background_tasks
        )
    else:
        return {"error": "File not found dummy"}

@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile):
    # Parse form data manually
    form = await request.form()
    session_uuid = form.get("session_uuid")
    trial_uuid = form.get("trial_uuid")
    trial_name = form.get("trial_name")
    cam_index = int(form.get("cam_index", 0))  # Default to 0 if not provided
    print(f"camera index is: {cam_index}")
    if trial_name == "calibration" or trial_name == "neutral":
        trial_uuid = trial_name
    session = sessionManager.findSessionByID(session_uuid)
    trial = Trial(name=trial_name, trial_uuid=trial_uuid)
    
    # Save file in chunks
    file_data = bytearray()
    while chunk := await file.read(1024 * 1024):  # Read 1 MB at a time
        file_data.extend(chunk)

    saved_path = fileManager.save_binary_file(data=bytes(file_data), session=session, cam_index=cam_index, trial=trial)
    print(f"Large file uploaded to {saved_path}")

    websocket = manager.find_web_connection_by_id(session_id=session_uuid)
    videoUploadedMsg = {
            "command": "video_uploaded",
            "session": session_uuid,
            "camera_index": cam_index
        }
    if websocket:
        await manager.send_personal_message(json.dumps(videoUploadedMsg), websocket=websocket)
    else:
        print("ERROR: Video uploaded but could not find web app websocket.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_type: str, link_to_web: Optional[str] = None ):
    await manager.connect(websocket, client_type, link_to_web)
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
                    #print(f"message received is: {message}")
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
                         asyncio.create_task( handle_web_message(
                            websocket, message_json, command, active_session, session_id
                        ))
                    else:
                        asyncio.create_task( handle_mobile_message(
                            websocket, message_json, command, active_session, session_id
                        ))

                elif "bytes" in data:
                    binary_data = data["bytes"]
                    print(f"Received binary data: {len(binary_data)} bytes")
                    save_binary_file(
                        binary_data,
                        f"received_file_cam{manager.find_websocket_index(websocket)}.mov"
                    )
                    await manager.broadcast(
                        f"Received binary data of size: {len(binary_data)} bytes",
                        session_id=session_id if session_id else None
                    )

    except WebSocketDisconnect:
        pass
    finally:
        if client_type == "mobile":
            # Inform the web app that a mobile disconnected.
            disconnectMsg = {
                "command": "mobile_disconnect",
            }
            await manager.broadcast(json.dumps(disconnectMsg), source=websocket)
        # Disconnect the websocket.
        manager.disconnect(websocket)
        logger.debug("A client is disconnecting")
       

async def handle_web_message(websocket, message_json, command, active_session: Session, session_id):
    print(f"Received command: {command}")
    if active_session:

        if command == 'process_trial':
            trialType = message_json.get("trialType")
            trialName = message_json.get("trialName")
            is_test = message_json.get("isTest")
            trialId = message_json.get("trialId")
            should_mirror = message_json.get("shouldMirror") # DEBUG!

            # To implement below:
            cameras_to_use = message_json.get("cameras_to_use")
            forceRedoPoseEstimation = message_json.get("forceRedoPoseEstimation")
            poseDetector = message_json.get("poseDetector")
            print(f"Debug: {cameras_to_use} should currently be None")
            if should_mirror:
                if trialType == "calibration":
                    active_session.add_camera(camera=active_session.iphoneModel["Cam0"], idx=1)
                    fileManager.save_session_metadata(active_session)
                print(f"{active_session}, trial: {trialName}, id: {trialId}")
                fileManager.mirror_recording(session=active_session, trialName=trialName, trialId=trialId, cam_index=0) #For debug!


            print("processing trial: ")


            await sessionManager.processTrial(websocket=websocket, session=active_session, trialId=trialId, trialType=trialType, isTest=is_test, trialNames=trialName, poseDetector=poseDetector, cameras_to_use=cameras_to_use)
        elif command == "reprocess_trial":
            trialType = message_json.get("trialType")
            trialName = message_json.get("trialName")
            trialId = message_json.get("trialId")

            forceRedoPoseEstimation = bool(message_json.get("forceRedoPoseEstimation") == "true")
            cameras_to_use = message_json.get("cameras_to_use")
            poseDetector = message_json.get("poseEstimator")
            resolution = message_json.get("resolution")

            print(f"[DEBUG] Trial Info - Type: {trialType}, Name: {trialName}, ID: {trialId}, "
                f"Force Redo: {forceRedoPoseEstimation}, Cameras: {cameras_to_use}, "
                f"Pose Estimator: {poseDetector}, Resolution: {resolution}")

            # await sessionManager.reProcessTrial() make this function!            

        elif command == "start_recording":
            trialType = message_json.get("trialType")
            is_test = message_json.get("isTest")
            trialName = message_json.get("trialName")
            if trialType == "calibration":
                # Add checkerboard info.
                rows = int(message_json.get("rows"))
                cols = int(message_json.get("cols"))
                square_size = float(message_json.get("squareSize"))
                placement = str(message_json.get("placement"))
                print(f"placement is: {placement} and is of type {type(placement)}")
                trialId = message_json.get("trialId")
                active_session.set_checkerboard_params(rows, cols, square_size, placement)
                fileManager.save_session_metadata(active_session)

            elif trialType == "neutral":
                subject = Subject.from_dict(message_json.get("subject"))
                sessionName = message_json.get("sessionName")
                active_session.set_subject(subject)
                trialId = message_json.get("trialId")
                active_session.set_name(sessionName)
                fileManager.save_session_metadata(active_session)

            elif trialType == "dynamic":
                newTrial = Trial(name=trialName) # Create new trial for the session.
                active_session.add_dynamic_trial(newTrial)
               # fileManager.create_trial_directory(session=active_session, trial=newTrial) Maybe not necessary.
                trialId = str(newTrial.uuid)
                print(f"new trial has ID: {trialId}")
                informWebAppMsg = {
                    "command": "new_dynamic_trialId",
                    "content": str(newTrial.uuid)
                }
                await manager.send_personal_message(message=json.dumps(informWebAppMsg), websocket=websocket)

            if is_test:
                print("running test recording which means I process a trial of the same type that would be recorded :)")
                #await sessionManager.processTrial(websocket=websocket, session=active_session, trialId=trialId, trialType = None, isTest=is_test, trialNames=None)
            await sessionManager.startRecording(websocket = websocket, session = active_session, trialId = trialId, trialType = trialType, trialName=trialName)

        elif command == "stop_recording":
            trialName = message_json.get("trialName")
            trialId = message_json.get("trialId")
            trialType = message_json.get("trialType")
            await sessionManager.sendStopTrial(websocket=websocket, session_id=str(active_session.uuid),trialName=trialName, trialType=trialType, trialId=trialId) # Should only come from dynamic trials.

        elif command == "get_session_trials":
            isTest = message_json.get("isTest")
            if isTest:
                trials = sessionManager.get_trials(session=Session(session_uuid="Giota"))
            else:
                trials = sessionManager.get_trials(session=active_session)
            jsonMsg = {
                "command": "sessionTrials",
                "content": trials,
                "session": str(active_session.uuid)
            }
            await manager.send_personal_message(message=json.dumps(jsonMsg), websocket=websocket)
        
        elif command == "get_max_video_count":

            videoCount = fileManager.get_session_max_cameras(session=active_session)

            print(f"DEBUG - Max videoCount for this session is {videoCount}")
            jsonMsg = {
                "command" : "maxVidCount",
                "content": videoCount
            }
            await manager.send_personal_message(message = json.dumps(jsonMsg), websocket= websocket)

        elif command == "get_visualizer":
            trialName = message_json.get("trialName")
            visualizerJson = fileManager.find_visualizer_json(session=active_session, trialName=trialName)
            jsonMsg = {
                "command": "visualizerJSON",
                "content": visualizerJson,
                "session": str(active_session.uuid)
            }
            await manager.send_personal_message(message=json.dumps(jsonMsg), websocket=websocket)
        
        elif command == "delete_session":
            idToDelete = message_json.get('content')
            fileManager.delete_session(session=Session(session_uuid=idToDelete))

        elif command == "download_session":
            #try:
            # Get chunk size and info egarding download. Send to web app
            print("zipped file")
            start_message = {
                    "command": "download_start",
                }
            await manager.send_personal_message(message=json.dumps(start_message), websocket=websocket)
            dataPath = fileManager.send_session_zip(session_id=str(active_session.uuid))
            fileName = os.path.basename(dataPath)
            
            # open the zipped file
            # Assuming you're sending this message via a WebSocket
            download_link = f"http://{ip_address}:8080/download/{fileName}"

            message = {
                "command": "download_link",
                "link": download_link
            }

            await manager.send_personal_message(message=json.dumps(message), websocket=websocket)

        elif command == "get_visualizer_videos":
            trialName = message_json.get("trialName")
            video_paths = fileManager.get_visualizer_videos(session = active_session, trialName=trialName)
            videos = []
            for video_path in video_paths:
                with open(video_path, "rb") as video:
                    encoded_video = base64.b64encode(video.read()).decode("utf-8")
                    videos.append({
                        "data": encoded_video
                    })
            message = {
                "command": "visualizer_videos",
                "content": videos
            }
            await manager.send_personal_message(json.dumps(message), websocket=websocket)
        elif command == "set_framerate":
            framerate = int(message_json.get("framerate"))
            response = {"command": "set_framerate", "trialType": "", "max_frame_rate": framerate, "session": str(active_session.uuid)}
            print(f"Sending to set framerate as {framerate}")
            await manager.broadcast(json.dumps(response), websocket) # Send to mobiles to change frame rate :)

        else:
            toastMsg = {
                "command": "Toast",
                "type": "Error",
                "content": f"Error: Unknown session-specific command '{command}"
            }
            await manager.send_personal_message(
                json.dumps(toastMsg), websocket
            )


    else:
        if command == "newSession":
            sessionManager.addSession(Session())
            session_id = sessionManager.activeSession.getID()
            manager.update_session_id(websocket=websocket, new_session_id=session_id)
            fileManager.create_session_directory(sessionManager.activeSession)
            manager.disconnect_mobiles(websocket=websocket)
            print("Connection is now:", manager.connections[websocket])
            newSessionMsg = {
                "command": "new_session",
                "content": str(session_id)
            }
            await manager.send_personal_message(json.dumps(newSessionMsg), websocket)

        if command == "change_session_id":
            session_id = message_json.get("session")
            manager.update_session_id(websocket=websocket, new_session_id=session_id)

        elif command == "get_subjects":
            loaded_subjects = [subject.to_dict() for subject in fileManager.load_subjects()]
            response = {"command": "subjects", "content": loaded_subjects}
            print(loaded_subjects)
            await manager.send_personal_message(json.dumps(response, default=str), websocket)

        elif command == "get_sessions":
            sessions = fileManager.find_sessions()

            response = {"command": "sessions", "content": sessions}
            #print(response)
            await manager.send_personal_message(json.dumps(response), websocket)
        elif command == "save_subject":
            subject = Subject.from_dict(message_json.get("content"))
            sessionManager.saveSubject(subject=subject)
        
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
        print("MOBILE CONNECTED")
        camera_model = str(message_json.get("content"))
        camera_maxframerate = str(message_json.get("max_frame_rate"))
        camera_index = manager.find_websocket_index(websocket)
        active_session.iphoneModel[f"Cam{camera_index}"] = camera_model
        message = {
            "command": "mobile_connected",
            "content": camera_index,
            "session": session_id,
            'maxFrameRate': camera_maxframerate #(inform webapp of the maxframerate of this device)
            }
        json_message = json.dumps(message)
        await manager.broadcast(json_message, websocket)
 
        answer = {
            "command": "new_camera_idx",
            "trialType": "", #Required by phone
            "camera_idx": camera_index,
            "session": session_id,
        }
        await manager.send_personal_message(json.dumps(answer), websocket=websocket)
        

    elif command == "save_video" and active_session:
        metadata = message_json.get("metadata", {})
        base64_data = message_json.get("videoData", "")
        trial_name = metadata.get("name")
        trialId = metadata.get("trialId") 
        trial = Trial(name=trial_name, trial_uuid=trialId)
        print(f"Saving video for trial: {trial}")
        camera_index = manager.find_websocket_index(websocket)
        video_data = base64.b64decode(base64_data)
        fileManager.save_binary_file(
            video_data, session=active_session, trial=trial, cam_index=camera_index
        )
        videoUploadedMsg = {
            "command": "video_uploaded",
            "session": session_id,
            "camera_index": camera_index
        }
        await manager.broadcast(json.dumps(videoUploadedMsg), source=websocket)

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

    #sessionManager.processingTrials["Dynamic_3"] = "processing"
    #sessionManager.processingTrials["Dynamic_1"] = "queued"


    fileManager.cleanEmptySessions()
    #ip_address = socket.gethostbyname(hostname) #"192.168.0.48"#socket.gethostbyname(hostname)
    #ip_address = "192.168.0.2"
    ip_address = "130.229.135.163" # ubuntu computer
    #ip_address = "192.168.50.9" Landet//
    print(f"IP Address: {ip_address}")

    uvicorn.run(app,
                host=ip_address,
                port=8080
                #ssl_certfile="cert.pem",
                #ssl_keyfile="key.pem"
                )