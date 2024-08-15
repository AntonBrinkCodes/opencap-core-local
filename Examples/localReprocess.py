"""
Attempt to fully locally process trials, no uploading to server.
First run calibration to get camera extrensics, then static trials to create opensim model,
Lastly run all dynamic trials.


"""
import os
import sys
sys.path.append(os.path.abspath('./..'))

from main import main

session_name = "4cf4bca5-7cd0-4db8-af11-5d39d485dba8" # aka session_ids in reprocessSessions.py

calib_id = "36598d50-4fd8-406d-8808-4e9df3cd0e84" # None (auto-selected trial), [] (skip), or string of specific trial_id
static_id = "ac82774d-b679-4a90-bce1-b3b768532503" # None (auto-selected trial), [] (skip), or string of specific trial_id
dynamic_trialNames = "ac82774d-b679-4a90-bce1-b3b768532503" # None (all dynamic trials), [] (skip), or list of trial names.
# OBS!!! Above are CaSE SenSIiVE
trial_Names = "neutral" # "calibration for extrinsic trials." neutral for static trials.
# Trial name for dynamic trials

poseDetector = 'openpose'

resolutionPoseDetection = '1x736'

extrinsicTrial = False
genericFolderNames = False
scaleModel = False

sessionType = "static" # Calibration, static, or dynamic. assumes dynamic if anything else


if sessionType == "calibration":
    extrinsicTrial = True
    genericFolderNames = True
elif sessionType == "static":
    scaleModel = True
    genericFolderNames=True


print(extrinsicTrial)
main(session_name, trial_Names, dynamic_trialNames, cameras_to_use=['all'],
         intrinsicsFinalFolder='Deployed', isDocker=False,
         extrinsicsTrial=extrinsicTrial,
         poseDetector='OpenPose', resolutionPoseDetection=resolutionPoseDetection,
         scaleModel=scaleModel, genericFolderNames = genericFolderNames)

# ScaleModel probably should only be true on calibration trial?
# extrinsicsTrial should be True on "Neutral". Which is probably to get extrinsics..



