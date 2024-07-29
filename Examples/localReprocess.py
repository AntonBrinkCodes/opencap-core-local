"""
Attempt to fully locally process trials, no uploading to server.
First run calibration to get camera extrensics, then static trials to create opensim model,
Lastly run all dynamic trials.


"""
import os
import sys
sys.path.append(os.path.abspath('./..'))

from main import main

session_name = "Giota" #Because thats what I named the folder :) aka session_ids in reprocessSessions.py

calib_id = "dynamic_1" # None (auto-selected trial), [] (skip), or string of specific trial_id
static_id = "neutral" # None (auto-selected trial), [] (skip), or string of specific trial_id
dynamic_trialNames = "Dynamic_2" # None (all dynamic trials), [] (skip), or list of trial names.
# OBS!!! Above are CaSE SenSIiVE

trial_Names = "dynamic_2" # "calibration for extrinsic trials." neutral for static trials.
# Trial name for dynamic trials

poseDetector = 'openpose'

resolutionPoseDetection = '1x736'

extrinsicTrial = False
genericFolderNames = False
scaleModel = False

sessionType = "dynamic" # Calibration, static, or dynamic. assumes dynamic if anything else


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



