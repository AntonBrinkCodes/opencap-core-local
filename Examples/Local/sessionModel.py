'''
Logic to control sessions, trials, etc when using the LocalCap webapp

-- Anton Brink 2024-07-31
'''

import uuid

import uuid
import yaml
from enum import Enum
from typing import List, Dict
from datetime import datetime

class sex(Enum):
    female = "f",
    male = "m",
    other = "o"

class Subject:
    """
        Initialize a Subject instance.

        Args:
            name (str): The name of the subject.
            sex (Sex): The sex of the subject, default is male.
            height (float): The height of the subject in meters.
            weight (float): The weight of the subject in kilograms.
    """
    def __init__(self, name="defaultSubject", sex=sex.male, height=1.89, weight=83.2):
        self.name=name
        self.sex = sex
        self.height = height #in meters
        self.weight = weight #in kilos



class Trial:
    """
        Initialize a Trial instance.

        Args:
            name (str): The name of the trial.
            videos (List): A list of videos associated with the trial.
    """
    def __init__(self, name, videos: List):
        self.name = name
        self.videos = videos

    def __repr__(self):
        return f"Trial(name={self.name}, data={self.videos})"


class Session:
    """
        Initialize a Session instance.

        Args:
            subject (Subject): The subject associated with the session.
            metadata (Optional[Dict]): Metadata for the session.
    """
    def __init__(self, subject: Subject=Subject()):
        self.subject = subject
        self.uuid = uuid.uuid4()
        self.dynamic_trials = []
        self.calibration_trial = None
        self.static_trial = None
        self.metadata = {}
        self.iphoneModel = {} # What type of cameras we have..
        self.createdAt = datetime.now()
        
        self.calibrationSettings : Dict[str, str] = {
            "overwriteDeployedIntrinsics": 'false',
            "saveSessionIntrinics": 'false',
        }

        self.checkerBoard: Dict[str, str] = {
            'black2BlackCornersHeight_n': 8,
            'black2BlackCornersWidth_n': 11,
            'placement': 'ground',
            'squareSideLength_mm': 60
        }

        self.markerAugmentationSettings: Dict[str, str] = {
              'markerAugmenterModel': 'LSTM'
        }

        self.openSimModel = 'LaiUhlrich2022'
    
    '''
    add the type of camera used (essentially what type of iPhone/iPad)
    '''
    def add_camera(self, camera: str, idx: int):
        """
        Add the type of camera used.

        Args:
            camera (str): The camera model.
            idx (int): The index of the camera.
        """
        self.iphoneModel[f'cam{idx}'] = camera

    def add_dynamic_trial(self, trial: Trial):
        """
        Add a dynamic trial to the session.

        Args:
            trial (Trial): The dynamic trial to be added.
        """
        self.dynamic_trials.append(trial)

    def set_calibration_trial(self, trial: Trial):
        """
        Set the calibration trial for the session.

        Args:
            trial (Trial): The calibration trial to be set.
        """
        self.calibration_trial = trial

    def set_static_trial(self, trial: Trial):
        """
        Set the static trial for the session.

        Args:
            trial (Trial): The static trial to be set.
        """
        self.static_trial = trial

    def save_metadata(self):
        metadata = {
            'uuid': str(self.uuid),
            'metadata': self.metadata,
            'dynamic_trials': [trial.name for trial in self.dynamic_trials],
            'calibration_trial': self.calibration_trial.name if self.calibration_trial else None,
            'static_trial': self.static_trial.name if self.static_trial else None
        }
        with open(self.metadata_file, 'w') as file:
            yaml.dump(metadata, file)

    def load_metadata(self):
        with open(self.metadata_file, 'r') as file:
            metadata = yaml.safe_load(file)
            self.uuid = uuid.UUID(metadata['uuid'])
            self.metadata = metadata['metadata']
            # Note: Loading of trials from names would require an additional mapping or method to recreate trials

    def __repr__(self):
        return (f"Session(uuid={self.uuid}, dynamic_trials={self.dynamic_trials}, "
                f"calibration_trial={self.calibration_trial}, static_trial={self.static_trial}, "
                f"metadata={self.metadata})")

    def getID(self):
        """
        Get the UUID of the session.

        Returns:
            UUID: The UUID of the session.
        """
        return self.uuid
# Example usage:
if __name__=="__main__":
    # Creating trials
    trial1 = Trial(name="Dynamic Trial 1", data={"duration": 5})
    trial2 = Trial(name="Dynamic Trial 2", data={"duration": 10})
    calibration_trial = Trial(name="Calibration Trial", data={"calibration_factor": 1.5})
    static_trial = Trial(name="Static Trial", data={"static_value": 42})

    # Creating a session with metadata
    session_metadata = {"experimenter": "Dr. Smith", "date": "2024-07-31"}
    session = Session(metadata=session_metadata)

    # Adding trials to the session
    session.add_dynamic_trial(trial1)
    session.add_dynamic_trial(trial2)
    session.set_calibration_trial(calibration_trial)
    session.set_static_trial(static_trial)

    # Saving session metadata to YAML file
    session.save_metadata()

    # Display the session
    print(session)

    # Loading session metadata from YAML file
