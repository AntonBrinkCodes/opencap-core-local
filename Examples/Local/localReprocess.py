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
from utils import deleteCalibrationFiles, deleteStaticFiles
from utils import getDataDirectory


def runLocalTrial(sessionId: str, trialNames, trialId, trialType="dynamic", poseDetector='hrnet', genericFolderNames=True, cameras_to_use=['all'],
                  resolutionPoseDetection='default', dataDir = None, forceRedoPoseEstimation = False) -> bool:
    '''
    Runs the trial Locally.

    Args:
        sessionID (str): The name of the session, usually a UUID.
        trialNames (any): # "calibration for extrinsic trials." neutral for static trials. # Trial name for dynamic trials
        trialId (any): None (all dynamic trials), [] (skip), or list of trial names. Trial names are the folder the trials are inside.
        trialType (str): "calibration" for calibration trials. "static" or "neutral" for neutral pose trials. "dynamic" for dynamic trials.
        poseDetector (str): "openpose" to use openpose. "hrnet" to use hrnet
        genericFolderNames (bool): Defaults to True. Whetever to use generic folder names or not.
        resolutionPoseDetection (str): Defaults to 'default'. The resolution to run openpose with. 
                                       NB: Higher resolutions than hardware supports will crash on Ubuntu and take a very long time on Windows (or maybe also crash).
        dataDir (str): Defaults to nullable.
    '''
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
        session_id = sessionId 
        data_dir = getDataDirectory(isDocker=False)
        session_path = os.path.join(data_dir,'Data',session_id)
        print(f"session_path is: {session_path}")    
        deleteCalibrationFiles(session_path=session_path, deleteRecorded=False)

        extrinsicTrial = True
    elif trialType == "static" or trialType=="neutral":
        data_dir = getDataDirectory(isDocker=False)
        session_path = os.path.join(data_dir,'Data', sessionId)
        print(f"session_path is: {session_path}")
        print(f"staticTrialname = {trialNames}")
        deleteStaticFiles(session_path=session_path, staticTrialName=trialNames)
        scaleModel = True
        forceRedoPoseEstimation = True


    main(sessionId, trialNames, trialId, cameras_to_use=cameras_to_use,
         intrinsicsFinalFolder='Deployed', isDocker=False,
          extrinsicsTrial=extrinsicTrial, poseDetector=poseDetector, resolutionPoseDetection=resolutionPoseDetection,
           scaleModel=scaleModel, genericFolderNames=genericFolderNames, forceRedoPoseEstimation=forceRedoPoseEstimation )
    
    return True


if __name__=="__main__":
    session_id = "27332dae-e4a6-40bb-8c58-2a34d5d3a0e4" #"4cf4bca5-7cd0-4db8-af11-5d39d485dba8" # aka session_ids in reprocessSessions.py

    calib_id = "dynamic"#"36598d50-4fd8-406d-8808-4e9df3cd0e84" # None (auto-selected trial), [] (skip), or string of specific trial_id
    static_id = "ac82774d-b679-4a90-bce1-b3b768532503" # None (auto-selected trial), [] (skip), or string of specific trial_id
    trial_id = "26964f1a-6eb0-44f1-ae28-fbe80d0e3fbc"#"afca93fd-9753-4bea-9130-5fdcf151d9f0" # None (all dynamic trials), [] (skip), or list of trial names. 
    # OBS!!! Above are CaSE Sensitive. trial_id are the names of the video files (a uuid)
    trial_Names = "s2_burpee_jump_forward" #calibration for extrinsic trials." neutral for static trials. NB: Name of the folder the trial are in actually,....
    # Trial name for dynamic trials

    poseDetector = 'hrnet' #OpenPose or hrnet

    resolutionPoseDetection = '1x736_2scales'#'1x736_2scales'

    extrinsicTrial = False
    genericFolderNames = True
    scaleModel = False

    sessionType = "dynamic" # Calibration, static, or dynamic. assumes dynamic if anything else
    forceRedoPoseEstimation = False #If pose estimation is performed for this poseestimatior and resolution, default is to use that result. This forces it to rerun if true
    os.chdir('..')
    if sessionType == "calibration":
         # Get session directory and delete previous calibration files output
        data_dir = getDataDirectory(isDocker=False)
        session_path = os.path.join(data_dir,'Data',session_id)
        print(f"session_path is: {session_path}")    
        deleteCalibrationFiles(session_path=session_path, deleteRecorded=False)

        extrinsicTrial = True
    elif sessionType == "static" or sessionType=="neutral":
        data_dir = getDataDirectory(isDocker=False)
        session_path = os.path.join(data_dir,'Data',session_id)
        deleteStaticFiles(session_path=session_path)
        scaleModel = True

    #os.chdir('..')
    
    print(extrinsicTrial)
    cameras_to_use=['Cam1', 'Cam2', 'Cam3'] #['all']
    main(session_id, trial_Names, trial_id, cameras_to_use=cameras_to_use,
             intrinsicsFinalFolder='Deployed', isDocker=False,
             extrinsicsTrial=extrinsicTrial,
             poseDetector=poseDetector, resolutionPoseDetection=resolutionPoseDetection,
             scaleModel=scaleModel, genericFolderNames = genericFolderNames, forceRedoPoseEstimation=True)

# ScaleModel probably should only be true on calibration trial?
# extrinsicsTrial should be True on "Neutral". Which is probably to get extrinsics..



