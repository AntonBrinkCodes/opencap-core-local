import os
from sessionModel import Session, Trial, Subject
from typing import List, Optional
import pickle
import json
import yaml
import uuid
import shutil
import base64

class FileManager:
    """
    Manage file organization for sessions, subjects and trials.
    """

    def __init__(self, base_directory: str):
        self.base_directory = base_directory
        print(base_directory)


    def create_cam_directory(self, session: Session, cam_index: int):
        cam_path = os.path.join(self.base_directory, str(session.uuid), 'Videos', f'Cam{cam_index}')
        os.makedirs(cam_path, exist_ok=True)
        return cam_path
    
    def create_session_directory(self, session: Session):
        session_path = os.path.join(self.base_directory, str(session.uuid), 'Videos')
        os.makedirs(session_path, exist_ok=True)
        for index,cam in enumerate(session.iphoneModel):
            self.create_cam_directory(session = session, cam_index = index)
        
        return session_path

    def create_trial_directory(self, session: Session, trial: Trial):
        for index, cam in enumerate(session.iphoneModel):
            trial_path = os.path.join(self.base_directory, str(session.uuid), 'Videos', f'Cam{index}', 'InputMedia', trial.name)
            os.makedirs(trial_path, exist_ok=True)
        return trial_path
    
    def save_session_metadata(self, session: Session):
        metadata_path = os.path.join(self.base_directory, str(session.uuid), 'sessionMetadata.yaml')
        session.save_metadata(metadata_file=metadata_path)

        return metadata_path

    def cleanEmptySessions(self):
        """
        Traverse through all subfolders of base_path, 
        check for empty 'Videos' folders and remove them along with their contents.

        :param base_path: Path to the base directory containing UUID-named folders.
        """
        # Iterate through each folder in the base_path
        for folder_name in os.listdir(self.base_directory):
            folder_path = os.path.join(self.base_directory, folder_name)

            # Check if it is a directory
            if os.path.isdir(folder_path):
                videos_folder = os.path.join(folder_path, "Videos")

                # Check if the 'Videos' folder exists
                if os.path.exists(videos_folder):
                    # Check if the 'Videos' folder is empty
                    if not os.listdir(videos_folder):  # Returns True if empty
                        print(f"Removing empty folder: {videos_folder}")
                        shutil.rmtree(folder_path)  # Remove the folder and all its contents

    def delete_session(self, session: Session)-> bool:
        """
        Deletes the folder corresponding to the given session and all its subfolders and files.

        Args:
            session (Session): The session whose folder is to be deleted.

        Returns:
            bool: True if the folder was successfully deleted, False if the folder did not exist.
        """
        session_path = os.path.join(self.base_directory, str(session.uuid))

        # Check if the session directory exists
        if os.path.exists(session_path):
            # Remove the session directory and its contents
            shutil.rmtree(session_path)
            print(f"Session folder {session_path} and all its contents have been deleted.")
            return True
        else:
            print(f"Session folder {session_path} does not exist.")
            return False

    def find_visualizer_json(self, session: Session, trialName: str):
        """
        Finds and loads the visualizer JSON file for a given trial and session.

        This function constructs the path to the visualizer JSON file using the session and trial UUIDs.
        It then reads the content of the JSON file and returns it as a dictionary.

        Args:
            session (Session): An instance of the Session class containing session details, including a UUID.
            trial (str): The name of the trial.

        Returns:
            dict: A dictionary containing the content of the visualizer JSON file.

        Raises:
            FileNotFoundError: If the specified JSON file does not exist at the constructed path.
            json.JSONDecodeError: If the file content is not a valid JSON.

        Example:
            >>> session = Session(uuid='12345')
            >>> trial = Trial(uuid='67890')
            >>> data = find_visualizer_json(self, session, trial)
            >>> print(data)
        """
        visualiser_path = os.path.join(self.base_directory, str(session.uuid), 'VisualizerJsons', trialName, f'{trialName}.json') #Should be name and not uuid. Pretty sure...
        #print(f'Path to visualizer JSON is: {visualiser_path}')
    
        # Read and return the JSON content
        with open(visualiser_path, 'r') as file:
            visualizer_data = json.load(file)
    
        return visualizer_data

    def find_sessions(self)-> dict:
        sessions_dict = {}  # Dictionary to hold metadata for each UUID folder

        # Iterate through each folder in the root directory
        for folder_name in os.listdir(self.base_directory):
            folder_path = os.path.join(self.base_directory, folder_name)
            print(folder_path)
            yaml.add_constructor(tag="tag:yaml.org,2002:python/object:uuid.UUID", constructor=uuid_constructor)

            # Check if the folder name matches a UUID pattern
            if os.path.isdir(folder_path):
                # Construct the path to sessionMetadata.yaml
                metadata_file_path = os.path.join(folder_path, 'sessionMetadata.yaml')

                # Check if sessionMetadata.yaml exists
                if os.path.isfile(metadata_file_path):
                    # Open and read the YAML file
                    with open(metadata_file_path, 'r') as file:
                        # Add the constructor for the UUID tag in YAML
                        metadata = yaml.safe_load(file)

                        # Extract specific lines or fields (modify as per your requirements)
                        # Assuming the YAML file has fields like 'session_name' and 'created_date'
                        session_info = {
                            "subjectName": metadata.get("subjectName", ""),
                            "sessionDate": metadata.get("sessionDate", ""),
                            "sessionID": metadata.get("sessionID", ""),
                            "mass": metadata.get("mass_kg", ""),
                            "height": metadata.get("height_m", "")
                            # Add other fields here as needed
                        }

                        # Add the extracted metadata to the sessions_dict with folder_name as key
                        sessions_dict[folder_name] = session_info

        return sessions_dict
    
    def save_binary_file(self, data: bytes, session: Session, cam_index: int, trial: Trial):
        """
        Save binary data to a file within the structured directories.

        Args:
            data (bytes): The binary data to save.
            session (Session): The session the data is associated with.
            cam_index (int): The camera index (X) for the CamX directory.
            trial (Trial): The trial the data is associated with.
            filename (str): The name of the file to save the data to.
        """
        # Create directories if they don't exist
        trial_path = self.create_trial_directory(session ,trial)
        trial_path = os.path.join(self.base_directory, str(session.uuid), 'Videos', f'Cam{cam_index}', 'InputMedia', trial.name) 
        filename = f"{str(trial.uuid)}.mov"
        # Full path for the file
        full_filename = os.path.join(trial_path, filename)

        # Save the binary data
        with open(full_filename, 'wb') as file:
            file.write(data)

        print(f"File saved as {full_filename}")

        # Check if the file was successfully saved
        if os.path.isfile(full_filename):  # Check if the file exists
            # Optionally check the file size
            if os.path.getsize(full_filename) > 0:  # Check if the file is not empty
                print(f"File saved successfully as {full_filename}")
            else:
                print(f"File saved as {full_filename} but it is empty.")
        else:
            print(f"Failed to save the file as {full_filename}.")

    def save_subjects(self, subjects: List[Subject]):
        """
        Save subjects to base_directoryt as a pickle file "subjects_data.pkl"

        Args:
            subjects (List[Subject]) a list of the Subjects to save to file
        """
        full_filename = os.path.join(self.base_directory, "subjects_data.pkl")
        with open(full_filename, 'wb') as file:
            pickle.dump(subjects, file)

    def load_subjects(self) -> List:
        """
        Load the subjects from pickle file created using save_subjects.

        Returns:
            subjects (List[Subject]) a list with all the Subjects saved in the file. Empty list if there is no file.
        """
        full_filename = os.path.join(self.base_directory, "subjects_data.pkl")
        if not os.path.exists(full_filename):
        # Return an empty list if the file does not exist
            return []
        
        with open(full_filename, 'rb') as file:
            loaded_subjects = pickle.load(file)
        return loaded_subjects
    
    def find_trials(self, session: Session)-> dict:
        """
        Finds and returns a dictionary containing information about the trials in a given session.
    
        This method scans through the specified session's directories to identify trials (excluding 'calibration') 
        and checks if they have been processed. The function populates a dictionary with each trial's status, 
        UUID, and associated .mov file name (without the extension).
    
        Args:
            session (Session): A session object containing the UUID to locate the relevant directories.
    
        Returns:
            dict: A dictionary where each key is the name of a trial (e.g., 'dynamic_1', 'neutral') and the value 
                  is another dictionary with the following keys:
                  - "processed" (bool): Indicates if the trial has been processed (exists in the processed trials folder).
                  - "uuid" (str or None): The name of the .mov file (excluding extension) if found, otherwise None.
    
        Example output:
            {
                'neutral': {
                    'processed': True,
                    'uuid': 'neutral_trial_UUID'
                },
                'dynamic_1': {
                    'processed': False,
                    'uuid': 'dynamic_1_trial_UUID'
                }
            }
        """
        trials_folder_path = os.path.join(self.base_directory, str(session.uuid), 'Videos', 'Cam0', 'InputMedia') #Cam0 always exists
        processed_trials_folder_path = os.path.join(self.base_directory, str(session.uuid), 'VisualizerJsons')
        # Should add also for visualizerVideos.
        trials = get_folders_in_path(trials_folder_path)
        processed_trials = get_folders_in_path(processed_trials_folder_path)


        # Create the dictionary to store trial information
        trial_dict = {}

        # Iterate over all trials except 'calibration'
        for trial in trials:
            if trial == 'calibration': # Skip it
                continue
            
            # Set initial entry in the dictionary
            trial_dict[trial] = {
                "processed": trial in processed_trials,
                "uuid": None,
                "trialName": trial,
            }

            # Define the trial directory path
            trial_path = os.path.join(trials_folder_path, trial)

            # Check if the directory exists
            if os.path.isdir(trial_path):
                # Get UUID from the directory name or file (if applicable)

                # Find the .mov file in the trial directory
                mov_files = [file for file in os.listdir(trial_path) if file.lower().endswith('.mov')]
                if mov_files:
                    # Store the first .mov file found (or modify as needed if there are multiple)
                    trial_dict[trial]['uuid'] = mov_files[0].rsplit(".",1)[0]

        # Return the final dictionary
        return trial_dict
    
    def zip_session_folder(self, session_id: str) -> str:
        # Path to the session folder
        session_folder_path = os.path.join(self.base_directory, session_id)
        zip_file_path = os.path(self.base_directory)

        # Create a zip file
        shutil.make_archive(zip_file_path.replace(".zip", ""), 'zip', session_folder_path)
        return zip_file_path
    
    def encode_zip_to_base64(self, zip_file_path: str) -> str:
        # Encode the zip file in base64
        with open(zip_file_path, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    def send_session_zip(self, session_id: str)-> str:

        # Zip the session folder
        zip_file_path = self.zip_session_folder(session_id)
        # Encode the zip file
        zip_data_base64 = self.encode_zip_to_base64(zip_file_path)
        
        # Send the zip file data over WebSocket
        # await websocket.send_json({
        #    "command": "download",
        #    "filename": f"{session_id}.zip",
        #    "filedata": zip_data_base64
        #})
        # Clean up the temporary zip file
        os.remove(zip_file_path)
        return zip_data_base64

def get_folders_in_path(path):
    return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

# Custom constructor for UUID
def uuid_constructor(loader, node):
    # Extract the value from the mapping node and create a UUID object
    value = loader.construct_mapping(node)
    return uuid.UUID(int=value['int'])

if __name__=="__main__": # FOR TESTING CLASS.
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_script_directory, '..'))
    base_directory = os.path.join(parent_directory, 'Data')

    fileManager = FileManager(base_directory)

    session = Session(session_uuid="4cf4bca5-7cd0-4db8-af11-5d39d485dba8")
    session = Session(session_uuid="123")
    trial = "s05-jumpingjacks_2_recording"
    fileManager.create_session_directory(session)
    print(fileManager.find_sessions())
    fileManager.delete_session(session=session)
    print(fileManager.find_trials(session=Session(session_uuid="Giota")))
    #visualizerJson = fileManager.find_visualizer_json(session, trial)
    #fileManager.cleanEmptySessions()
    #print(fileManager.find_sessions())
    #print(fileManager.find_trials(session=Session(session_uuid="Giota")))