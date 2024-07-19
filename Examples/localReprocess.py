"""
Attempt to fully locally process trials, no uploading to server.


"""
import os
import sys
sys.path.append(os.path.abspath('./..'))

from main import main

session_name = "sessionName" #Because thats what I named the folder :) aka session_ids in reprocessSessions.py

calib_id = None # None (auto-selected trial), [] (skip), or string of specific trial_id
static_id = None # None (auto-selected trial), [] (skip), or string of specific trial_id
dynamic_trialNames = '416171ae-c500-4ccf-bbdb-d44108d2ed17' # None (all dynamic trials), [] (skip), or list of trial names MAYBE THIS SHOULD BE THE WEIRD NUMBERS..

trial_Names = "neutral"

poseDetector = 'openpose'

resolutionPoseDetection = '1x736_2scales'

main(session_name, trial_Names, dynamic_trialNames, cameras_to_use=['all'],
         intrinsicsFinalFolder='Deployed', isDocker=False,
         extrinsicsTrial=False,
         poseDetector='OpenPose', resolutionPoseDetection=resolutionPoseDetection,
         scaleModel=True)

# ScaleModel probably should only be true on calibration trial?
# extrinsicsTrial should be True on "Neutral". Which is probably to get extrinsics..



