import os
from sessionModel import Session, Trial, Subject
from typing import List, Optional
import pickle
import json
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


    def find_visualizer_json(self, session: Session, trial: Trial):
        """
        Finds and loads the visualizer JSON file for a given trial and session.

        This function constructs the path to the visualizer JSON file using the session and trial UUIDs.
        It then reads the content of the JSON file and returns it as a dictionary.

        Args:
            session (Session): An instance of the Session class containing session details, including a UUID.
            trial (Trial): An instance of the Trial class containing trial details, including a UUID.

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
        visualiser_path = os.path.join(self.base_directory, str(session.uuid), 'VisualizerJsons', trial.name, f'{trial.name}.json') #Should be name and not uuid. Pretty sure...
        print(f'Path to visualizer JSON is: {visualiser_path}')
    
        # Read and return the JSON content
        with open(visualiser_path, 'r') as file:
            visualizer_data = json.load(file)
    
        return visualizer_data

    
    
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
    


if __name__=="__main__": # FOR TESTING CLASS.
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_script_directory, '..'))
    base_directory = os.path.join(parent_directory, 'Data')

    fileManager = FileManager(base_directory)

    session = Session(session_uuid="4cf4bca5-7cd0-4db8-af11-5d39d485dba8")
    trial = Trial(name="s05-jumpingjacks_2_recording")

    visualizerJson = fileManager.find_visualizer_json(session, trial)