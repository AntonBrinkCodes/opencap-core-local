"""
Attempt to fully locally process trials, no uploading to server.
First run calibration to get camera extrensics, then static trials to create opensim model,
Lastly run all dynamic trials.

TODO: Add some type of throw error depending on if main succeeds or not.
"""
import os
import sys

# Dynamically calculate to get main folder.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from main import main
from utils import deleteCalibrationFiles
from utils import getDataDirectory


def runLocalTrial(sessionId: str, trialNames, trialId, trialType="dynamic", poseDetector='openpose', genericFolderNames=True, cameras_to_use=['all'],
                  resolutionPoseDetection='default', dataDir = None) -> bool:
    
    if dataDir:
        os.chdir(dataDir)
        # Check if the current folder is named "Data"
        if os.path.basename(os.getcwd()) == "Data":
        # Change the directory one level up if it is "Data"
            os.chdir("..")

    extrinsicTrial = False
    scaleModel = False

    if trialType == "calibration":
         # Get session directory and delete previous calibration files output
        session_name = sessionId 
        data_dir = getDataDirectory(isDocker=False)
        session_path = os.path.join(data_dir,'Data',session_name)
        print(f"session_path is: {session_path}")    
        deleteCalibrationFiles(session_path=session_path, deleteRecorded=False)

        extrinsicTrial = True
    elif trialType == "static" or trialType=="neutral":
        scaleModel = True


    main(sessionId, trialNames, trialId, cameras_to_use=cameras_to_use,
         intrinsicsFinalFolder='Deployed', isDocker=False,
          extrinsicsTrial=extrinsicTrial, poseDetector=poseDetector, resolutionPoseDetection=resolutionPoseDetection,
           scaleModel=scaleModel, genericFolderNames=genericFolderNames )
    
    return True


if __name__=="__main__":
    session_name = "4cf4bca5-7cd0-4db8-af11-5d39d485dba8" # aka session_ids in reprocessSessions.py

    calib_id = "36598d50-4fd8-406d-8808-4e9df3cd0e84" # None (auto-selected trial), [] (skip), or string of specific trial_id
    static_id = "ac82774d-b679-4a90-bce1-b3b768532503" # None (auto-selected trial), [] (skip), or string of specific trial_id
    dynamic_trialNames = "afca93fd-9753-4bea-9130-5fdcf151d9f0" # None (all dynamic trials), [] (skip), or list of trial names.
    # OBS!!! Above are CaSE Sensitive. dynamic_trialNames are the names of the video files (a uuid)
    trial_Names = "s05-treadmill_1_recording" # "calibration for extrinsic trials." neutral for static trials.
    # Trial name for dynamic trials

    poseDetector = 'openpose'

    resolutionPoseDetection = '1x736_2scales'

    extrinsicTrial = False
    genericFolderNames = True
    scaleModel = False

    sessionType = "dynamic" # Calibration, static, or dynamic. assumes dynamic if anything else



    os.chdir('..')

    print(extrinsicTrial)
    main(session_name, trial_Names, dynamic_trialNames, cameras_to_use=['all'],
             intrinsicsFinalFolder='Deployed', isDocker=False,
             extrinsicsTrial=extrinsicTrial,
             poseDetector='OpenPose', resolutionPoseDetection=resolutionPoseDetection,
             scaleModel=scaleModel, genericFolderNames = genericFolderNames)

# ScaleModel probably should only be true on calibration trial?
# extrinsicsTrial should be True on "Neutral". Which is probably to get extrinsics..



