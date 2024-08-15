import os
from sessionModel import Session, Trial, Subject
from typing import List, Optional
class FileManager:
    """
    Manage file organization for sessions and trials.
    """
    def __init__(self, base_directory: str):
        self.base_directory = base_directory

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