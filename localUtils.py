import os
import numpy as np
import pickle
import yaml
import socket
import subprocess
import cv2
import copy
import json
import utilsDataman

def getVideoExtension(pathFileWithoutExtension):
    
    pathVideoDir = os.path.split(pathFileWithoutExtension)[0]
    videoName = os.path.split(pathFileWithoutExtension)[1]
    for file in os.listdir(pathVideoDir):
        if videoName == file.rsplit('.', 1)[0]:
            extension = '.' + file.rsplit('.', 1)[1]
            
    return extension


def loadCameraParameters(filename):
    open_file = open(filename, "rb")
    cameraParams = pickle.load(open_file)
    
    open_file.close()
    return cameraParams

def importMetadata(filePath):
    myYamlFile = open(filePath)
    parsedYamlFile = yaml.load(myYamlFile, Loader=yaml.FullLoader)
    
    return parsedYamlFile


def getMMposeDirectory(isDocker=False):
    computername = socket.gethostname()
    
    # Paths to OpenPose folder for local testing.
    if computername == "clarkadmin-MS-7996":
        mmposeDirectory = "/home/clarkadmin/Documents/MyRepositories/MoVi_analysis/model_ckpts"
    else:
        mmposeDirectory = ''
    return mmposeDirectory


def getOpenPoseDirectory(isDocker=False):
    computername = os.environ.get('COMPUTERNAME', None)
    print('COMPUTER NAME IS {}', computername)
    # Paths to OpenPose folder for local testing.
    if computername == "DESKTOP-0UPR1OH":
        openPoseDirectory = "C:/Software/openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended/openpose"
    elif computername == "HPL1":
        openPoseDirectory = "C:/Users/opencap/Documents/MySoftware/openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended/openpose"
    elif computername == "DESKTOP-GUEOBL2":
        openPoseDirectory = "C:/Software/openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended/openpose"
    elif computername == "DESKTOP-L9OQ0MS":
        openPoseDirectory = "C:/Software/openpose-1.7.0-binaries-win64-gpu-python3.7-flir-3d_recommended/openpose"
    elif isDocker:
        openPoseDirectory = "docker"
    elif computername == 'SUHLRICHHPLDESK':
        openPoseDirectory = "C:/openpose/"
    elif computername == "LAPTOP-7EDI4Q8Q":
        openPoseDirectory = "C:/openpose/"
    elif computername == "DESKTOP-NJMGEBG":
        openPoseDirectory = "C:/openpose/"
    elif computername == None:
	    print("Inside None case in getOpenPoseDirectory()")
	    openPoseDirectory = "/home/anton/openpose/"
    else:
        openPoseDirectory = "C:/openpose/"
    return openPoseDirectory


def getDataDirectory(isDocker=False):
    computername = socket.gethostname()
    # Paths to OpenPose folder for local testing.
    if computername == 'SUHLRICHHPLDESK':
        dataDir = 'C:/Users/scott.uhlrich/MyDrive/mobilecap/'
    elif computername == "LAPTOP-7EDI4Q8Q":
        dataDir = 'C:\MyDriveSym/mobilecap/'
    elif computername == 'DESKTOP-0UPR1OH':
        dataDir = 'C:/Users/antoi/Documents/MyRepositories/mobilecap_data/'
    elif computername == 'HPL1':
        dataDir = 'C:/Users/opencap/Documents/MyRepositories/mobilecap_data/'
    elif computername == 'DESKTOP-GUEOBL2':
        dataDir = 'C:/Users/opencap/Documents/MyRepositories/mobilecap_data/'
    elif computername == 'DESKTOP-L9OQ0MS':
        dataDir = 'C:/Users/antoi/Documents/MyRepositories/mobilecap_data/'
    elif computername == 'clarkadmin-MS-7996':
        dataDir = '/home/clarkadmin/Documents/MyRepositories/mobilecap_data/'
    elif computername == 'DESKTOP-NJMGEBG':
        dataDir = 'C:/Users/opencap/Documents/MyRepositories/mobilecap_data/'
    elif isDocker:
        dataDir = os.getcwd()
    else:
        dataDir = os.getcwd()
    return dataDir


## Local Utils Checker

def saveCameraParameters(filename,CameraParams):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename),exist_ok=True)
    
    open_file = open(filename, "wb")
    pickle.dump(CameraParams, open_file)
    open_file.close()
    
    return True

def calcIntrinsics(folderName, CheckerBoardParams=None, filenames=['*.jpg'], 
                   imageScaleFactor=1, visualize=False, saveFileName=None):
    if CheckerBoardParams is None:
        # number of black to black corners and side length (cm)
        CheckerBoardParams = {'dimensions': (6,9), 'squareSize': 2.71}
    
    if '*' in filenames[0]:
        imageFiles = glob.glob(folderName + '/' + filenames[0])
        
    else:
        imageFiles = [] ;
        for fName in filenames:
            imageFiles.append(folderName + '/' + fName)    
           
    # stop the iteration when specified 
    # accuracy, epsilon, is reached or 
    # specified number of iterations are completed. 
    criteria = (cv2.TERM_CRITERIA_EPS + 
                cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)       
      
    # Vector for 3D points 
    threedpoints = [] 
      
    # Vector for 2D points 
    twodpoints = []       
      
    #  3D points real world coordinates 
    # objectp3d = generate3Dgrid(CheckerBoardParams) 
            
    # Load images in for calibration
    for iImage, pathName in enumerate(imageFiles):
        image = cv2.imread(pathName) 
        if imageScaleFactor != 1:
            dim = (int(imageScaleFactor*image.shape[1]),int(imageScaleFactor*image.shape[0]))
            image = cv2.resize(image,dim,interpolation=cv2.INTER_AREA)
        imageSize = np.reshape(np.asarray(np.shape(image)[0:2]).astype(np.float64),(2,1)) # This all to be able to copy camera param dictionary
        
        grayColor = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
        print(pathName + ' used for intrinsics calibration.')
      
        # Find the chess board corners 
        # If desired number of corners are 
        # found in the image then ret = true 
        # ret, corners = cv2.findChessboardCorners( 
        #                 grayColor, CheckerBoardParams['dimensions'],  
        #                 cv2.CALIB_CB_ADAPTIVE_THRESH
        #                 + cv2.CALIB_CB_FAST_CHECK + 
        #                 cv2.CALIB_CB_NORMALIZE_IMAGE) 
        
        ret,corners,meta = cv2.findChessboardCornersSBWithMeta(	grayColor, CheckerBoardParams['dimensions'],
                                                        cv2.CALIB_CB_EXHAUSTIVE + 
                                                        cv2.CALIB_CB_ACCURACY + 
                                                        cv2.CALIB_CB_LARGER)
      
        # If desired number of corners can be detected then, 
        # refine the pixel coordinates and display 
        # them on the images of checker board 
        if ret == True: 
            # 3D points real world coordinates 
            checkerCopy = copy.copy(CheckerBoardParams)
            checkerCopy['dimensions'] = meta.shape[::-1] # reverses order so width is first
            objectp3d = generate3Dgrid(checkerCopy)
            
            threedpoints.append(objectp3d) 
      
            # Refining pixel coordinates 
            # for given 2d points. 
            # corners2 = cv2.cornerSubPix( 
            #     grayColor, corners, (11, 11), (-1, -1), criteria) 
            
            corners2 = corners/imageScaleFactor # Don't need subpixel refinement with findChessboardCornersSBWithMeta
            twodpoints.append(corners2) 
            
            # Draw and display the corners 
            image = cv2.drawChessboardCorners(image,  
                                                meta.shape[::-1],  
                                                corners2, ret) 
                
            #findAspectRatio
            ar = imageSize[1]/imageSize[0]            
            # cv2.namedWindow("img", cv2.WINDOW_NORMAL) 
            cv2.resize(image,(int(600*ar),600))
            
            # Save intrinsic images
            imageSaveDir = os.path.join(folderName,'IntrinsicCheckerboards')
            if not os.path.exists(imageSaveDir):
                os.mkdir(imageSaveDir)
            cv2.imwrite(os.path.join(imageSaveDir,'intrinsicCheckerboard' + str(iImage) + '.jpg'), image)
                
            if visualize:
                print('Press enter or close image to continue')
                cv2.imshow('img', image) 
                cv2.waitKey(0)  
                cv2.destroyAllWindows() 
                
        if ret == False:
            print("Couldn't find checkerboard in " + pathName)
  
    if len(twodpoints) < .5*len(imageFiles):
       print('Checkerboard not detected in at least half of intrinsic images. Re-record video.')
       return None
       
     
    # Perform camera calibration by 
    # passing the value of above found out 3D points (threedpoints) 
    # and its corresponding pixel coordinates of the 
    # detected corners (twodpoints) 
    ret, matrix, distortion, r_vecs, t_vecs = cv2.calibrateCamera( 
        threedpoints, twodpoints, grayColor.shape[::-1], None, None)     
    
    CamParams = {'distortion':distortion,'intrinsicMat':matrix,'imageSize':imageSize}
    
    if saveFileName is not None:
        saveCameraParameters(saveFileName,CamParams)
  
    return CamParams

def calcExtrinsicsFromVideo(videoPath, CamParams, CheckerBoardParams,
                            visualize=False, imageUpsampleFactor=2,
                            useSecondExtrinsicsSolution=False):    
    # Get video parameters.
    vidLength = getVideoLength(videoPath)
    videoDir, videoName = os.path.split(videoPath)    
    # Pick end of video as only sample point. For some reason, won't output
    # video with t close to vidLength, so we count down til it does.
    tSampPts = [np.round(vidLength-0.3, decimals=1)]    
    upsampleIters = 0
    for iTime,t in enumerate(tSampPts):
        # Pop an image.
        imagePath = os.path.join(videoDir, 'extrinsicImage0.png')
        if os.path.exists(imagePath):
            os.remove(imagePath)
        while not os.path.exists(imagePath) and t>=0:
            video2Images(videoPath, nImages=1, tSingleImage=t, filePrefix='extrinsicImage', skipIfRun=False)
            t -= 0.2
        # Default to beginning if can't find a keyframe.
        if not os.path.exists(imagePath):
            video2Images(videoPath, nImages=1, tSingleImage=0.01, filePrefix='extrinsicImage', skipIfRun=False)
        # Throw error if it can't find a keyframe.
        if not os.path.exists(imagePath):
            exception = 'No calibration image could be extracted for at least one camera. Verify your setup and try again. Visit https://www.opencap.ai/best-pratices to learn more about camera calibration and https://www.opencap.ai/troubleshooting for potential causes for a failed calibration.'
            raise Exception(exception, exception)
        # Try to find the checkerboard; return None if you can't find it.           
        CamParamsTemp = calcExtrinsics(
            os.path.join(videoDir, 'extrinsicImage0.png'),
            CamParams, CheckerBoardParams, visualize=visualize, 
            imageUpsampleFactor=imageUpsampleFactor,
            useSecondExtrinsicsSolution=useSecondExtrinsicsSolution)
        while iTime == 0 and CamParamsTemp is None and upsampleIters < 3:
            if imageUpsampleFactor > 1: 
                imageUpsampleFactor = 1
            elif imageUpsampleFactor == 1:
                imageUpsampleFactor = .5
            elif imageUpsampleFactor < 1:
                imageUpsampleFactor = 1
            CamParamsTemp = calcExtrinsics(
                os.path.join(videoDir, 'extrinsicImage0.png'),
                CamParams, CheckerBoardParams, visualize=visualize, 
                imageUpsampleFactor=imageUpsampleFactor,
                useSecondExtrinsicsSolution=useSecondExtrinsicsSolution)
            upsampleIters += 1
        if CamParamsTemp is not None:
            # If checkerboard was found, exit.
            CamParams = CamParamsTemp.copy()
            return CamParams

    # If made it through but didn't return camera params, throw an error.
    exception = 'The checkerboard was not detected by at least one camera. Verify your setup and try again. Visit https://www.opencap.ai/best-pratices to learn more about camera calibration and https://www.opencap.ai/troubleshooting for potential causes for a failed calibration.'
    raise Exception(exception, exception)
    
    return None

def generate3Dgrid(CheckerBoardParams):
    #  3D points real world coordinates. Assuming z=0
    objectp3d = np.zeros((1, CheckerBoardParams['dimensions'][0]  
                          * CheckerBoardParams['dimensions'][1],  
                          3), np.float32) 
    objectp3d[0, :, :2] = np.mgrid[0:CheckerBoardParams['dimensions'][0], 
                                    0:CheckerBoardParams['dimensions'][1]].T.reshape(-1, 2) 
    
    objectp3d = objectp3d * CheckerBoardParams['squareSize'] 
    
    return objectp3d

def isCheckerboardUpsideDown(CameraParams):
    # With backwall orientation, R[1,1] will always be positive in correct orientation
    # and negative if upside down
    for cam in list(CameraParams.keys()):
        if CameraParams[cam] is not None:
            upsideDown = CameraParams[cam]['rotation'][1,1] < 0
            break
        #Default if no camera params (which is a garbage case anyway)
        upsideDown = False

    return upsideDown

def getVideoLength(filename):
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)

# %%
def video2Images(videoPath, nImages=12, tSingleImage=None, filePrefix='output', skipIfRun=True, outputFolder='default'):
    # Pops images out of a video.
    # If tSingleImage is defined (time, not frame number), only one image will be popped
    if outputFolder == 'default':
        outputFolder = os.path.dirname(videoPath)
    
    # already written out?
    if not os.path.exists(os.path.join(outputFolder, filePrefix + '_0.jpg')) or not skipIfRun: 
        if tSingleImage is not None: # pop single image at time value
            CMD = ('ffmpeg -loglevel error -skip_frame nokey -y -ss ' + str(tSingleImage) + ' -i ' + videoPath + 
                   " -qmin 1 -q:v 1 -frames:v 1 -vf select='-eq(pict_type\,I)' " + 
                   os.path.join(outputFolder,filePrefix + '0.png'))
            os.system(CMD)
            outImagePath = os.path.join(outputFolder,filePrefix + '0.png')
           
        else: # pop multiple images from video
            lengthVideo = getVideoLength(videoPath)
            timeImageSamples = np.linspace(1,lengthVideo-1,nImages) # disregard first and last second
            for iFrame,t_image in enumerate(timeImageSamples):
                CMD = ('ffmpeg -loglevel error -skip_frame nokey -ss ' + str(t_image) + ' -i ' + videoPath + 
                       " -qmin 1 -q:v 1 -frames:v 1 -vf select='-eq(pict_type\,I)' " + 
                       os.path.join(outputFolder,filePrefix) + '_' + str(iFrame) + '.jpg')
                os.system(CMD)
                outImagePath = os.path.join(outputFolder,filePrefix) + '0.jpg'
                
    return outImagePath

def calcExtrinsics(imageFileName, CameraParams, CheckerBoardParams,
                   imageScaleFactor=1,visualize=False,
                   imageUpsampleFactor=1,useSecondExtrinsicsSolution=False):
    # Camera parameters is a dictionary with intrinsics
    
    # stop the iteration when specified 
    # accuracy, epsilon, is reached or 
    # specified number of iterations are completed. 
    criteria = (cv2.TERM_CRITERIA_EPS + 
                cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001) 
      
    # Vector for 3D points 
    threedpoints = [] 
      
    # Vector for 2D points 
    twodpoints = [] 
    
    #  3D points real world coordinates. Assuming z=0
    objectp3d = generate3Dgrid(CheckerBoardParams)
    
    # Load and resize image - remember calibration image res needs to be same as all processing
    image = cv2.imread(imageFileName)
    if imageScaleFactor != 1:
        dim = (int(imageScaleFactor*image.shape[1]),int(imageScaleFactor*image.shape[0]))
        image = cv2.resize(image,dim,interpolation=cv2.INTER_AREA)
        
    if imageUpsampleFactor != 1:
        dim = (int(imageUpsampleFactor*image.shape[1]),int(imageUpsampleFactor*image.shape[0]))
        imageUpsampled = cv2.resize(image,dim,interpolation=cv2.INTER_AREA)
    else:
        imageUpsampled = image

    
    # Find the chess board corners 
    # If desired number of corners are 
    # found in the image then ret = true 
    
    #TODO need to add a timeout to the findChessboardCorners function
    grayColor = cv2.cvtColor(imageUpsampled, cv2.COLOR_BGR2GRAY)
    
    ## Contrast TESTING - openCV does thresholding already, but this may be a bit helpful for bumping contrast
    # grayColor = grayColor.astype('float64')
    # cv2.imshow('Grayscale', grayColor.astype('uint8'))
    # savePath = os.path.join(os.path.dirname(imageFileName),'extrinsicGray.jpg')
    # cv2.imwrite(savePath,grayColor)
    
    # grayContrast = np.power(grayColor,2)
    # grayContrast = grayContrast/(np.max(grayContrast)/255)    
    # # plt.figure()
    # # plt.imshow(grayContrast, cmap='gray')
    
    # # cv2.imshow('ContrastEnhanced', grayContrast.astype('uint8'))
    # savePath = os.path.join(os.path.dirname(imageFileName),'extrinsicGrayContrastEnhanced.jpg')
    # cv2.imwrite(savePath,grayContrast)
      
    # grayContrast = grayContrast.astype('uint8')
    # grayColor = grayColor.astype('uint8')

    ## End contrast Testing
    
    ## Testing settings - slow and don't help 
    # ret, corners = cv2.findChessboardCorners( 
    #                 grayContrast, CheckerBoardParams['dimensions'],  
    #                 cv2.CALIB_CB_ADAPTIVE_THRESH  
    #                 + cv2.CALIB_CB_FAST_CHECK + 
    #                 cv2.CALIB_CB_NORMALIZE_IMAGE) 
    
    # Note I tried findChessboardCornersSB here, but it didn't find chessboard as reliably
    ret, corners = cv2.findChessboardCorners( 
                grayColor, CheckerBoardParams['dimensions'],  
                cv2.CALIB_CB_ADAPTIVE_THRESH) 

    # If desired number of corners can be detected then, 
    # refine the pixel coordinates and display 
    # them on the images of checker board 
    if ret == True: 
        # 3D points real world coordinates       
        threedpoints.append(objectp3d) 
  
        # Refining pixel coordinates 
        # for given 2d points. 
        corners2 = cv2.cornerSubPix( 
            grayColor, corners, (11, 11), (-1, -1), criteria) / imageUpsampleFactor
  
        twodpoints.append(corners2) 
  
        # For testing: Draw and display the corners 
        # image = cv2.drawChessboardCorners(image,  
        #                                  CheckerBoardParams['dimensions'],  
        #                                   corners2, ret) 
        # Draw small dots instead
        # Choose dot size based on size of squares in pixels
        circleSize = 1
        squareSize = np.linalg.norm((corners2[1,0,:] - corners2[0,0,:]).squeeze())
        if squareSize >12:
            circleSize = 2

        for iPoint in range(corners2.shape[0]):
            thisPt = corners2[iPoint,:,:].squeeze()
            cv2.circle(image, tuple(thisPt.astype(int)), circleSize, (255,255,0), 2) 
        
        #cv2.imshow('img', image) 
        #cv2.waitKey(0) 
  
        #cv2.destroyAllWindows()
    if ret == False:
        print('No checkerboard detected. Will skip cam in triangulation.')
        return None
        
        
    # Find position and rotation of camera in board frame.
    # ret, rvec, tvec = cv2.solvePnP(objectp3d, corners2,
    #                                CameraParams['intrinsicMat'], 
    #                                CameraParams['distortion'])
    
    # This function gives two possible solutions.
    # It helps with the ambiguous cases with small checkerboards (appears like
    # left handed coord system). Unfortunately, there isn't a clear way to 
    # choose the correct solution. It is the nature of the solvePnP problem 
    # with a bit of 2D point noise.
    rets, rvecs, tvecs, reprojError = cv2.solvePnPGeneric(
        objectp3d, corners2, CameraParams['intrinsicMat'], 
        CameraParams['distortion'], flags=cv2.SOLVEPNP_IPPE)
    rvec = rvecs[1]
    tvec = tvecs[1]
   
    if rets < 1 or np.max(rvec) == 0 or np.max(tvec) == 0:
        print('solvePnPGeneric failed. Use SolvePnPRansac')
        # Note: can input extrinsics guess if we generally know where they are.
        # Add to lists to look like solvePnPRansac results
        rvecs = []
        tvecs = []
        ret, rvec, tvec, inliers = cv2.solvePnPRansac(
            objectp3d, corners2, CameraParams['intrinsicMat'],
            CameraParams['distortion'])
        if ret is True:
            rets = 1
            rvecs.append(rvec)
            tvecs.append(tvec)
        else:
            print('Extrinsic calculation failed. Will skip cam in triangulation.')
            return None
    
    # Select which extrinsics solution to use
    extrinsicsSolutionToUse = 0
    if useSecondExtrinsicsSolution:
        extrinsicsSolutionToUse = 1
        
    topLevelExtrinsicImageFolder = os.path.abspath(
        os.path.join(os.path.dirname(imageFileName),
                     '../../../../CalibrationImages'))
    if not os.path.exists(topLevelExtrinsicImageFolder):
        os.makedirs(topLevelExtrinsicImageFolder,exist_ok=True)
        
    for iRet,rvec,tvec in zip(range(rets),rvecs,tvecs):
        theseCameraParams = copy.deepcopy(CameraParams)
        # Show reprojections
        img_points, _ = cv2.projectPoints(objectp3d, rvec, tvec, 
                                          CameraParams['intrinsicMat'],  
                                          CameraParams['distortion'])
    
        # Plot reprojected points
        # for c in img_points.squeeze():
        #     cv2.circle(image, tuple(c.astype(int)), 2, (0, 255, 0), 2)
        
        # Show object coordinate system
        imageCopy = copy.deepcopy(image)
        imageWithFrame = cv2.drawFrameAxes(
            imageCopy, CameraParams['intrinsicMat'], 
            CameraParams['distortion'], rvec, tvec, 200, 4)
        
        # Create zoomed version.
        ht = image.shape[0]
        wd = image.shape[1]
        bufferVal = 0.05 * np.mean([ht,wd])
        topEdge = int(np.max([np.squeeze(np.min(img_points,axis=0))[1]-bufferVal,0]))
        leftEdge = int(np.max([np.squeeze(np.min(img_points,axis=0))[0]-bufferVal,0]))
        bottomEdge = int(np.min([np.squeeze(np.max(img_points,axis=0))[1]+bufferVal,ht]))
        rightEdge = int(np.min([np.squeeze(np.max(img_points,axis=0))[0]+bufferVal,wd]))
        
        # imageCopy2 = copy.deepcopy(imageWithFrame)
        imageCropped = imageCopy[topEdge:bottomEdge,leftEdge:rightEdge,:]
                
        
        # Save extrinsics picture with axis
        imageSize = np.shape(image)[0:2]
        #findAspectRatio
        ar = imageSize[1]/imageSize[0]
        # cv2.namedWindow("axis", cv2.WINDOW_NORMAL) 
        cv2.resize(imageWithFrame,(600,int(np.round(600*ar))))
     
        # save crop image to local camera file
        savePath2 = os.path.join(os.path.dirname(imageFileName), 
                                'extrinsicCalib_soln{}.jpg'.format(iRet))
        cv2.imwrite(savePath2,imageCropped)
          
        if visualize:   
            print('Close image window to continue')
            cv2.imshow('axis', image)
            cv2.waitKey()
            
            cv2.destroyAllWindows()
        
        R_worldFromCamera = cv2.Rodrigues(rvec)[0]
        
        theseCameraParams['rotation'] = R_worldFromCamera
        theseCameraParams['translation'] = tvec
        theseCameraParams['rotation_EulerAngles'] = rvec
        
        # save extrinsics parameters to video folder
        # will save the selected parameters in Camera folder in main
        saveExtPath = os.path.join(
            os.path.dirname(imageFileName),
            'cameraIntrinsicsExtrinsics_soln{}.pickle'.format(iRet))
        saveCameraParameters(saveExtPath,theseCameraParams)
        
        # save images to top level folder and return correct extrinsics
        camName = os.path.split(os.path.abspath(
                  os.path.join(os.path.dirname(imageFileName), '../../')))[1] 
            
        if iRet == extrinsicsSolutionToUse:
            fullCamName = camName 
            CameraParamsToUse = copy.deepcopy(theseCameraParams)
        else:
            fullCamName = 'altSoln_{}'.format(camName)
        savePath = os.path.join(topLevelExtrinsicImageFolder, 'extrinsicCalib_' 
                                + fullCamName + '.jpg')
        cv2.imwrite(savePath,imageCropped)   
            
    return CameraParamsToUse


def autoSelectExtrinsicSolution(sessionDir,keypoints2D,confidence,extrinsicsOptions):
    keypoints2D = copy.copy(keypoints2D)
    confidence = copy.copy(confidence)
       
    camNames = list(extrinsicsOptions.keys()) 
    
    optimalCalibrationDict = {}
    
    # Order the cameras based on biggest difference between solutions. Want to start
    # with these
    if len(camNames)>2:
        camNames = orderCamerasForAutoCalDetection(extrinsicsOptions)
    
    # Find first pair of cameras
    optimalCalibrationDict[camNames[0]], optimalCalibrationDict[camNames[1]] = computeOptimalCalibrationCombination(
        keypoints2D,confidence,extrinsicsOptions,[camNames[0],camNames[1]])
    
    # Continue for third and additional cameras
    additionalCameras = []
    if len(camNames)>2:
        additionalCameras = camNames[2:]
    
    for camName in additionalCameras:
        _, optimalCalibrationDict[camName] = computeOptimalCalibrationCombination(
        keypoints2D,confidence,extrinsicsOptions,[camNames[0],camName],
        firstCamSoln=optimalCalibrationDict[camNames[0]])
    
    # save calibrationJson to Videos
    calibrationOptionsFile = os.path.join(sessionDir,'Videos','calibOptionSelections.json')
    with open(calibrationOptionsFile, 'w') as f:
        json.dump(optimalCalibrationDict, f)
    f.close()
    
    # Make camera params dict
    CamParamDict = {}
    for camName in camNames:
        CamParamDict[camName] = extrinsicsOptions[camName][optimalCalibrationDict[camName]]
        
    # Switch any cameras in local file system. 
    for cam,val in optimalCalibrationDict.items():
        if val == 1:
            saveFileName = os.path.join(sessionDir,'Videos',cam,'cameraIntrinsicsExtrinsics.pickle')
            saveCameraParameters(saveFileName,extrinsicsOptions[cam][1])
    
    return CamParamDict

# %%
def orderCamerasForAutoCalDetection(extrinsicsOptions):
    # dict of rotations between first and second solutions
    rotDifs = []
    testVec = np.array((1,0,0))
    for cals in extrinsicsOptions.values():
        rot = np.matmul(cals[0]['rotation'],cals[1]['rotation'])
        # This will be close to 0 if the rotation was small, 2 if it is 180
        rotDifs.append(1-np.dot(np.matmul(testVec,rot),testVec))
    
    sortedCams = [cam for _, cam in sorted(zip(rotDifs, extrinsicsOptions.keys()),reverse=True)]
    
    return sortedCams


# %%
def computeOptimalCalibrationCombination(keypoints2D,confidence,extrinsicsOptions,
                                         CamNames,firstCamSoln=None):
    if firstCamSoln is None:
        firstCamOptions = range(len(extrinsicsOptions[CamNames[0]]))
    else:
        firstCamOptions = [firstCamSoln]
        
    # Remove face markers - they are intermittent.
    _, idxFaceMarkers = getOpenPoseFaceMarkers()
    
    #find most confident frame
    confidenceMat = np.minimum(confidence[CamNames[0]],confidence[CamNames[1]])
    confidenceMat = np.delete(confidenceMat, idxFaceMarkers,axis=0)
    iFrame = np.argmax(confidenceMat.mean(axis=1))
    
    # put keypoints in list and delete face markers
    keypointList = [np.expand_dims(np.delete(keypoints2D[CamNames[0]],idxFaceMarkers,axis=0)[:,iFrame],axis=1),
                    np.expand_dims(np.delete(keypoints2D[CamNames[1]],idxFaceMarkers,axis=0)[:,iFrame],axis=1)]
    
    meanReprojectionErrors = []
    combinations = []  
    
    for iCam0 in firstCamOptions:
        for iCam1 in range(len(extrinsicsOptions[CamNames[1]])):
            combinations.append([iCam0,iCam1])
            
            CameraParamList = [extrinsicsOptions[CamNames[0]][iCam0],
                               extrinsicsOptions[CamNames[1]][iCam1]]
                                           
            # triangulate           
            points3D,_ = triangulateMultiview(CameraParamList,keypointList)
            
            # reproject
            # Make list of camera objects
            cameraObjList = []       
            for camParams in CameraParamList:
                c = Camera()
                c.set_K(camParams['intrinsicMat'])
                c.set_R(camParams['rotation'])
                c.set_t(np.reshape(camParams['translation'],(3,1)))
                cameraObjList.append(c)
               
            # Organize points for reprojectionError function
            stackedPoints = np.stack([k[:,None,0,:] for k in keypointList])
            pointsInput = []
            for i in range(stackedPoints.shape[1]):
                pointsInput.append(stackedPoints[:,i,0,:].T)
           
            # Calculate combined reprojection error
            reprojError = calcReprojectionError(cameraObjList,pointsInput,points3D,
                                                normalizeError=True)
            meanReprojectionErrors.append(np.mean(reprojError))
      
    # Select solution with minimum error
    idx = np.argmin(meanReprojectionErrors)
    
    if (sorted(meanReprojectionErrors)[1]-sorted(meanReprojectionErrors)[0])/sorted(meanReprojectionErrors)[0] < .5:
        # This only happens when the vector from checker board origin to camera is < a few degrees. If you offset the board
        # vertically by a few feet, the solution becomes very clear again (ratio of ~7). We could throw an error.
        print("Warning: not much separability between auto checker board selection options. Try moving checkerboard closer to cameras, and move it so it is not straight-on with any of the cameras.")
        # Pick default to first solution when they are super close like this.
        idx = 0
        
    return combinations[idx][0], combinations[idx][1]

def TRC2numpy(pathFile, markers,rotation=None):
    # rotation is a dict, eg. {'y':90} with axis, angle for rotation
    
    trc_file = utilsDataman.TRCFile(pathFile)
    time = trc_file.time
    num_frames = time.shape[0]
    data = np.zeros((num_frames, len(markers)*3))
    
    if rotation != None:
        for axis,angle in rotation.items():
            trc_file.rotate(axis,angle)
    for count, marker in enumerate(markers):
        data[:,3*count:3*count+3] = trc_file.marker(marker)    
    this_dat = np.empty((num_frames, 1))
    this_dat[:, 0] = time
    data_out = np.concatenate((this_dat, data), axis=1)
    
    return data_out

def getOpenPoseMarkerNames():
    
    markerNames = ["Nose", "Neck", "RShoulder", "RElbow", "RWrist",
                   "LShoulder", "LElbow", "LWrist", "midHip", "RHip",
                   "RKnee", "RAnkle", "LHip", "LKnee", "LAnkle", "REye",
                   "LEye", "REar", "LEar", "LBigToe", "LSmallToe",
                   "LHeel", "RBigToe", "RSmallToe", "RHeel"]
    
    return markerNames

def getOpenPoseFaceMarkers():
    
    faceMarkerNames = ['Nose', 'REye', 'LEye', 'REar', 'LEar']
    markerNames = getOpenPoseMarkerNames()
    idxFaceMarkers = [markerNames.index(i) for i in faceMarkerNames]
    
    return faceMarkerNames, idxFaceMarkers

def getMMposeMarkerNames():
    
    markerNames = ["Nose", "LEye", "REye", "LEar", "REar", "LShoulder", 
                   "RShoulder", "LElbow", "RElbow", "LWrist", "RWrist",
                   "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle",
                   "LBigToe", "LSmallToe", "LHeel", "RBigToe", "RSmallToe",
                   "RHeel"]        
    
    return markerNames

def synchronizeVideos(CameraDirectories, trialRelativePath, pathPoseDetector,
                      undistortPoints=False, CamParamDict=None, 
                      confidenceThreshold=0.3, 
                      filtFreqs={'gait':12,'default':30},
                      imageBasedTracker=False, cams2Use=['all'],
                      poseDetector='OpenPose', trialName=None, bbox_thr=0.8,
                      resolutionPoseDetection='default', 
                      visualizeKeypointAnimation=False):
    
    markerNames = getOpenPoseMarkerNames()
    
    # Create list of cameras.
    if cams2Use[0] == 'all':
        cameras2Use = list(CameraDirectories.keys())
    else:
        cameras2Use = cams2Use
    cameras2Use_in = copy.deepcopy(cameras2Use)

    # Initialize output lists
    pointList = []
    confList = []
    
    CameraDirectories_selectedCams = {}
    CamParamList_selectedCams = []
    for cam in cameras2Use:
        CameraDirectories_selectedCams[cam] = CameraDirectories[cam]
        CamParamList_selectedCams.append(CamParamDict[cam])
        
    # Load data.
    camsToExclude = []
    for camName in CameraDirectories_selectedCams:
        cameraDirectory = CameraDirectories_selectedCams[camName]
        videoFullPath = os.path.normpath(os.path.join(cameraDirectory,
                                                      trialRelativePath))
        trialPrefix, _ = os.path.splitext(
            os.path.basename(trialRelativePath))
        if poseDetector == 'OpenPose':
            outputPklFolder = "OutputPkl_" + resolutionPoseDetection
        elif poseDetector == 'mmpose':
            outputPklFolder = "OutputPkl_mmpose_" + str(bbox_thr)
        openposePklDir = os.path.join(outputPklFolder, trialName)
        pathOutputPkl = os.path.join(cameraDirectory, openposePklDir)
        ppPklPath = os.path.join(pathOutputPkl, trialPrefix+'_rotated_pp.pkl')
        key2D, confidence = loadPklVideo(
            ppPklPath, videoFullPath, imageBasedTracker=imageBasedTracker,
            poseDetector=poseDetector,confidenceThresholdForBB=0.3)
        thisVideo = cv2.VideoCapture(videoFullPath.replace('.mov', '_rotated.avi'))
        frameRate = np.round(thisVideo.get(cv2.CAP_PROP_FPS))        
        if key2D.shape[1] == 0 and confidence.shape[1] == 0:
            camsToExclude.append(camName)
        else:
            pointList.append(key2D)
            confList.append(confidence)
        
    # If video is not existing, the corresponding camera should be removed.
    idx_camToExclude = []
    for camToExclude in camsToExclude:
        cameras2Use.remove(camToExclude)
        CameraDirectories_selectedCams.pop(camToExclude)
        idx_camToExclude.append(cameras2Use_in.index(camToExclude))
        # By removing the cameras in CamParamDict and CameraDirectories, we
        # modify those dicts in main, which is needed for the next stages.
        CamParamDict.pop(camToExclude)
        CameraDirectories.pop(camToExclude)        
    delete_multiple_element(CamParamList_selectedCams, idx_camToExclude)    

    # Creates a web animation for each camera's keypoints. For debugging.
    if visualizeKeypointAnimation:
        import plotly.express as px
        import plotly.io as pio
        pio.renderers.default = 'browser'
    
        for i,data in enumerate(pointList):
        
            nPoints,nFrames,_ = data.shape
            # Reshape the 3D numpy array to 2D, preserving point and frame indices
            data_reshaped = np.copy(data).reshape(-1, 2)
    
            # Create DataFrame
            df = pd.DataFrame(data_reshaped, columns=['x', 'y'])
    
            # Add columns for point number and frame number
            df['Point'] = np.repeat(np.arange(nPoints), nFrames)
            df['Frame'] = np.tile(np.arange(nFrames), nPoints)
    
            # Reorder columns if needed
            df = df[['Point', 'Frame', 'x', 'y']]
               
            # Create a figure and add an animated scatter plot
            fig = px.scatter(df,x='x', y='y', title="Cam " + str(i),
                              animation_frame='Frame',
                              range_x=[0, 1200], range_y=[1200,0],
                              color='Point', color_continuous_scale=px.colors.sequential.Viridis)
    
            # Show the animation
            fig.show()

    # Synchronize keypoints.
    pointList, confList, nansInOutList,startEndFrameList = synchronizeVideoKeypoints(
        pointList, confList, confidenceThreshold=confidenceThreshold,
        filtFreqs=filtFreqs, sampleFreq=frameRate, visualize=False,
        maxShiftSteps=2*frameRate, CameraParams=CamParamList_selectedCams,
        cameras2Use=cameras2Use, 
        CameraDirectories=CameraDirectories_selectedCams, trialName=trialName)
    
    if undistortPoints:
        if CamParamList_selectedCams is None:
            raise Exception('Need to have CamParamList to undistort Images')
        # nFrames = pointList[0].shape[1]
        unpackedPoints = unpackKeypointList(pointList) ;
        undistortedPoints = []
        for points in unpackedPoints:
            undistortedPoints.append(undistort2Dkeypoints(
                points, CamParamList_selectedCams, useIntrinsicMatAsP=True))
        pointList = repackKeypointList(undistortedPoints)
        
    pointDir = {}
    confDir = {}
    nansInOutDir = {}
    startEndFrames = {}
    for iCam, camName in enumerate(CameraDirectories_selectedCams):
        pointDir[camName] =  pointList[iCam]
        confDir[camName] =  confList[iCam] 
        nansInOutDir[camName] = nansInOutList[iCam] 
        startEndFrames[camName] = startEndFrameList[iCam]
        
    return pointDir, confDir, markerNames, frameRate, nansInOutDir, startEndFrames, cameras2Use

 %%
def synchronizeVideoKeypoints(keypointList, confidenceList,
                              confidenceThreshold=0.3, 
                              filtFreqs = {'gait':12,'default':500},
                              sampleFreq=30, visualize=False, maxShiftSteps=30,
                              isGait=False, CameraParams = None,
                              cameras2Use=['none'],CameraDirectories = None,
                              trialName=None, trialID=''):
    visualize2Dkeypoint = False # this is a visualization just for testing what filtered input data looks like
    
    # keypointList is a mCamera length list of (nmkrs,nTimesteps,2) arrays of camera 2D keypoints
    print('Synchronizing Keypoints')
    
    # Deep copies such that the inputs do not get modified.
    c_CameraParams = copy.deepcopy(CameraParams)
    c_cameras2Use = copy.deepcopy(cameras2Use)
    c_CameraDirectoryDict = copy.deepcopy(CameraDirectories)
    
    # Turn Camera Dict into List
    c_CameraDirectories = list(c_CameraDirectoryDict.values())
    # Check if one camera has only 0s as confidence scores, which would mean
    # no one has been properly identified. We want to kick out this camera
    # from the synchronization and triangulation. We do that by popping out
    # the corresponding data before syncing and add back 0s later.
    badCameras = []
    for icam, conf in enumerate(confidenceList):
        if np.max(conf) == 0.0:
            badCameras.append(icam)
    idxBadCameras = [badCameras[i]-i for i in range(len(badCameras))]
    cameras2NotUse = []
    for idxBadCamera in idxBadCameras:
        print('{} kicked out of synchronization'.format(
            c_cameras2Use[idxBadCamera]))
        cameras2NotUse.append(c_cameras2Use[idxBadCamera])
        keypointList.pop(idxBadCamera)
        confidenceList.pop(idxBadCamera)
        c_CameraParams.pop(idxBadCamera)
        c_cameras2Use.pop(idxBadCamera)
        c_CameraDirectories.pop(idxBadCamera)
        
        
    markerNames = getOpenPoseMarkerNames()
    mkrDict = {mkr:iMkr for iMkr,mkr in enumerate(markerNames)}
    
    # First, remove occluded markers
    footMkrs = {'right':[mkrDict['RBigToe'], mkrDict['RSmallToe'], mkrDict['RHeel'],mkrDict['RAnkle']],
                'left':[mkrDict['LBigToe'], mkrDict['LSmallToe'], mkrDict['LHeel'],mkrDict['LAnkle']]}
    armMkrs = {'right':[mkrDict['RElbow'], mkrDict['RWrist']],
                'left':[mkrDict['LElbow'], mkrDict['LWrist']]}
    
    plt.close('all')
    
    # Copy for visualization
    keypointListUnfilt = copy.deepcopy(keypointList)
    
    # remove occluded foot markers (uses large differences in confidence)
    keypointList,confidenceList = zip(*[removeOccludedSide(keys,conf,footMkrs,confidenceThreshold,visualize=False) for keys,conf in zip(keypointList,confidenceList)])
    # remove occluded arm markers
    keypointList,confidenceList = zip(*[removeOccludedSide(keys,conf,armMkrs,confidenceThreshold,visualize=False) for keys,conf in zip(keypointList,confidenceList)])
       
    # Copy for visualization 
    keypointListOcclusionRemoved = copy.deepcopy(keypointList)
    
    # Don't change these. The ankle markers are used for gait detector
    markers4VertVel = [mkrDict['RAnkle'], mkrDict['LAnkle']] # R&L Ankles and Heels did best. There are some issues though - like when foot marker velocity is aligned with camera ray
    markers4HandPunch = [mkrDict['RWrist'], mkrDict['LWrist'],mkrDict['RShoulder'],mkrDict['LShoulder']]
    markers4Ankles = [mkrDict['RAnkle'],mkrDict['LAnkle']]
    
    # find velocity signals for synchronization
    nCams = len(keypointList)
    vertVelList = []
    mkrSpeedList = []
    handPunchVertPositionList = []
    allMarkerList = []
    for (keyRaw,conf) in zip(keypointList,confidenceList):
        keyRaw_clean, _, _, _ = clean2Dkeypoints(keyRaw,conf,confidenceThreshold=0.3,nCams=nCams,linearInterp=True)        
        keyRaw_clean_smooth = smoothKeypoints(keyRaw_clean, sdKernel=3) 
        handPunchVertPositionList.append(getPositions(keyRaw_clean_smooth,markers4HandPunch,direction=1)) 
        vertVelList.append(getVertVelocity(keyRaw_clean_smooth)) # doing it again b/c these settings work well for synchronization
        mkrSpeedList.append(getMarkerSpeed(keyRaw_clean_smooth,markers4VertVel,confidence=conf,averageVels=False)) # doing it again b/c these settings work well for synchronization
        allMarkerList.append(keyRaw_clean_smooth)
        
    # Find indices with high confidence that overlap between cameras.    
    # Note: Could get creative and do camera pair syncing in the future, based
    # on cameras with greatest amount of overlapping confidence.
    overlapInds_clean, minConfLength_all = findOverlap(confidenceList,
                                                   markers4VertVel)
    
    # If no overlap found, try with fewer cameras.
    c_nCams = len(confidenceList)
    while not np.any(overlapInds_clean) and c_nCams>2:
        print("Could not find overlap with {} cameras - trying with {} cameras".format(c_nCams, c_nCams-1))
        cam_list = [i for i in range(nCams)]
        # All possible combination with c_nCams-1 cameras.
        from itertools import combinations
        combs = set(combinations(cam_list, c_nCams-1))
        overlapInds_clean_combs = []
        for comb in combs:
            confidenceList_sel = [confidenceList[i] for i in list(comb)]
            overlapInds_clean_c, minConfLength_c = findOverlap(
                confidenceList_sel, markers4VertVel)
            overlapInds_clean_combs.append(overlapInds_clean_c.flatten())
        longest_stretch = 0
        for overlapInds_clean_comb in overlapInds_clean_combs:
            stretch_size = overlapInds_clean_comb.shape[0]
            if stretch_size > longest_stretch:
                longest_stretch = stretch_size
                overlapInds_clean = overlapInds_clean_comb
        c_nCams -= 1
        
    # If no overlap found, return 0s.
    if not np.any(overlapInds_clean):
        keypointsSync = []
        confidenceSync = []
        nansInOutSync = []
        for i in range(len(cameras2Use)):
            keypointsSync.insert(i, np.zeros((keypointList[0].shape[0], 10,
                                              keypointList[0].shape[2])))
            confidenceSync.insert(i, np.zeros((keypointList[0].shape[0], 10)))
            nansInOutSync.insert(i, np.array([np.nan, np.nan]))     
        return keypointsSync, confidenceSync, nansInOutSync
                
    [idxStart, idxEnd] = [np.min(overlapInds_clean), np.max(overlapInds_clean)]
    idxEnd += 1 # Python indexing system.
    # Take max shift between cameras into account.
    idxStart = int(np.max([0,idxStart - maxShiftSteps]))
    idxEnd = int(np.min([idxEnd+maxShiftSteps,minConfLength_all]))
    # Re-sample the lists    
    vertVelList = [v[idxStart:idxEnd] for v in vertVelList]
    mkrSpeedList = [v[:,idxStart:idxEnd] for v in mkrSpeedList]
    handPunchVertPositionList = [p[:,idxStart:idxEnd] for p in handPunchVertPositionList]
    allMarkerList = [p[:,idxStart:idxEnd] for p in allMarkerList]
    confSyncList= [c[:,idxStart:idxEnd] for c in confidenceList]
    
    # We do this again, since it might have changed after finding the overlap period.
    keypointList = list(keypointList)
    confidenceList = list(confidenceList)
    badCamerasOverlap = []
    for icam, conf in enumerate(confSyncList):
        if np.mean(conf) <= 0.01: # Looser than sum=0 to disregard very few frames with data
            badCamerasOverlap.append(icam)
    idxbadCamerasOverlap = [badCamerasOverlap[i]-i for i in range(len(badCamerasOverlap))]
    for idxbadCameraOverlap in idxbadCamerasOverlap:
        print('{} kicked out of synchronization - after overlap check'.format(
            c_cameras2Use[idxbadCameraOverlap]))
        cameras2NotUse.append(c_cameras2Use[idxbadCameraOverlap])
        keypointList.pop(idxbadCameraOverlap)
        confidenceList.pop(idxbadCameraOverlap)
        c_CameraParams.pop(idxbadCameraOverlap)
        c_cameras2Use.pop(idxbadCameraOverlap)
        c_CameraDirectories.pop(idxbadCameraOverlap)
        
        vertVelList.pop(idxbadCameraOverlap)
        mkrSpeedList.pop(idxbadCameraOverlap)
        handPunchVertPositionList.pop(idxbadCameraOverlap)
        allMarkerList.pop(idxbadCameraOverlap)
        confSyncList.pop(idxbadCameraOverlap)        
    nCams = len(keypointList)
    
    # Detect whether it is a gait trial, which determines what sync algorithm
    # to use. Input right and left ankle marker speeds. Gait should be
    # detected for all cameras (all but one camera is > 2 cameras) for the
    # trial to be considered a gait trial.
    try:
        isGait = detectGaitAllVideos(mkrSpeedList,allMarkerList,confSyncList,markers4Ankles,sampleFreq)
    except:
        isGait = False
        print('Detect gait activity algorithm failed.')
    
    # Detect activity, which determines sync function that gets used
    isHandPunch,handForPunch = detectHandPunchAllVideos(handPunchVertPositionList,sampleFreq)
    if isHandPunch:
        syncActivity = 'handPunch'
    elif isGait:
        syncActivity = 'gait'
    else:
        syncActivity = 'general'
        
    print('Using ' + syncActivity + ' sync function.')
    
    
    # Select filtering frequency based on if it is gait
    if isGait: 
        filtFreq = filtFreqs['gait']
    else: 
        filtFreq = filtFreqs['default']
    
    # Filter keypoint data
    # sdKernel = sampleFreq/(2*np.pi*filtFreq) # not currently used, but in case using gaussian smoother (smoothKeypoints function) instead of butterworth to filter keypoints
    keyFiltList = []
    confFiltList = []
    confSyncFiltList = []
    nansInOutList = []
    for (keyRaw,conf) in zip(keypointList,confidenceList):
        keyRaw_clean, conf_clean, nans_in_out, conf_sync_clean = clean2Dkeypoints(keyRaw,conf,confidenceThreshold,nCams=nCams)
        keyRaw_clean_filt = filterKeypointsButterworth(keyRaw_clean,filtFreq,sampleFreq,order=4)
        keyFiltList.append(keyRaw_clean_filt)
        confFiltList.append(conf_clean)
        confSyncFiltList.append(conf_sync_clean)
        nansInOutList.append(nans_in_out)

    # Copy for visualization
    keypointListFilt = copy.deepcopy(keyFiltList)
    confidenceListFilt = copy.deepcopy(confFiltList)
    confidenceSyncListFilt = copy.deepcopy(confSyncFiltList)

    # find nSample shift relative to the first camera
    # nSamps = keypointList[0].shape[1]
    shiftVals = []
    shiftVals.append(0)
    timeVecs = []
    tStartEndVec = np.zeros((len(keypointList),2))
    for iCam,vertVel in enumerate(vertVelList):
        timeVecs.append(np.arange(keypointList[iCam].shape[1]))
        if iCam>0:
            # if no keypoints in Cam0 or the camera of interest, do not use cross_corr to sync.
            if np.max(np.abs(vertVelList[iCam])) == 0 or np.max(np.abs(vertVelList[0])) == 0:
                lag = 0
            elif syncActivity == 'general':
                dataForReproj = {'CamParamList':c_CameraParams,
                                 'keypointList':keypointListFilt,
                                 'cams2UseReproj': [0, c_cameras2Use.index(c_cameras2Use[iCam])],
                                 'confidence': confidenceSyncListFilt,
                                 'cameras2Use': c_cameras2Use
                                 }
                corVal,lag = cross_corr(vertVel,vertVelList[0],multCorrGaussianStd=maxShiftSteps/2,
                                        visualize=False,dataForReproj=dataForReproj,
                                        frameRate=sampleFreq) # gaussian curve gets multipled by correlation plot - helping choose the smallest shift value for periodic motions
            elif syncActivity == 'gait':
                
                dataForReproj = {'CamParamList':c_CameraParams,
                                 'keypointList':keypointListFilt,
                                 'cams2UseReproj': [0, c_cameras2Use.index(c_cameras2Use[iCam])],
                                 'confidence': confidenceSyncListFilt,
                                 'cameras2Use': c_cameras2Use
                                 }
                corVal,lag = cross_corr_multiple_timeseries(mkrSpeedList[iCam],
                                            mkrSpeedList[0],
                                            multCorrGaussianStd=maxShiftSteps/2,
                                            dataForReproj=dataForReproj,
                                            visualize=False,
                                            frameRate=sampleFreq)    
            elif syncActivity == 'handPunch':
                corVal,lag = syncHandPunch([handPunchVertPositionList[i] for i in [0,iCam]],
                                           handForPunch,maxShiftSteps=maxShiftSteps)
            if np.abs(lag) > maxShiftSteps: # if this fails and we get a lag greater than maxShiftSteps (units=timesteps)
                lag = 0 
                print('Did not use cross correlation to sync {} - computed shift was greater than specified {} frames. Shift set to 0.'.format(c_cameras2Use[iCam], maxShiftSteps))
            shiftVals.append(lag)
            timeVecs[iCam] = timeVecs[iCam] - shiftVals[iCam]
        tStartEndVec[iCam,:] = [timeVecs[iCam][0], timeVecs[iCam][-1]]
        
    # align signals - will start at the latest-starting frame (most negative shift) and end at
    # nFrames - the end of the earliest starting frame (nFrames - max shift)
    tStart = np.max(tStartEndVec[:,0])
    tEnd = np.min(tStartEndVec[:,1])
    
    keypointsSync = []
    confidenceSync = []
    startEndFrames = []
    nansInOutSync = []
    for iCam,key in enumerate(keyFiltList):
        # Trim the keypoints and confidence lists
        confidence = confFiltList[iCam]
        iStart = int(np.argwhere(timeVecs[iCam]==tStart))
        iEnd = int(np.argwhere(timeVecs[iCam]==tEnd))
        keypointsSync.append(key[:,iStart:iEnd+1,:])
        confidenceSync.append(confidence[:,iStart:iEnd+1])
        if shiftVals[iCam] > 0:
            shiftednNansInOut = nansInOutList[iCam] - shiftVals[iCam]
        else:
            shiftednNansInOut = nansInOutList[iCam]
        nansInOutSync.append(shiftednNansInOut)        
        # Save start and end frames to list, so can rewrite videos in
        # triangulateMultiviewVideo
        startEndFrames.append([iStart,iEnd])
        
    # Plot synchronized velocity curves
    if visualize:
        # Vert Velocity
        f, (ax0,ax1) = plt.subplots(1,2)
        for (timeVec,vertVel) in zip(timeVecs,vertVelList):
            ax0.plot(timeVec[range(len(vertVel))],vertVel)
        legNames = [c_cameras2Use[iCam] for iCam in range(len(vertVelList))]
        ax0.legend(legNames)
        ax0.set_title('summed vertical velocities')
        
        # Marker speed
        for (timeVec,mkrSpeed) in zip(timeVecs,mkrSpeedList):
            ax1.plot(timeVec[range(len(vertVel))],mkrSpeed[2])
        legNames = [c_cameras2Use[iCam] for iCam in range(len(vertVelList))]
        ax1.legend(legNames)
        ax1.set_title('Right Ankle Speed')
    
    # Plot a single marker trajectory to see effect of filtering and occlusion removal
    if visualize2Dkeypoint:
        nCams = len(keypointListFilt)
        nCols = int(np.ceil(nCams/2))
        mkr = mkrDict['RBigToe']
        mkrXY = 0 # x=0, y=1
        
        fig = plt.figure()
        fig.set_size_inches(12,7,forward=True)
        for camNum in range(nCams):
            ax = plt.subplot(2,nCols,camNum+1)
            ax.set_title(c_cameras2Use[iCam])
            ax.set_ylabel('yPos (pixel)')
            ax.set_xlabel('frame')
            ax.plot(keypointListUnfilt[camNum][mkr,:,mkrXY],linewidth = 2)
            ax.plot(keypointListOcclusionRemoved[camNum][mkr,:,mkrXY],linewidth=1.6)
            ax.plot(keypointListFilt[camNum][mkr,:,mkrXY],linewidth=1.3)
            
            # find indices where conf> thresh or nan (the marker is used in triangulation)
            usedInds = np.argwhere(np.logical_or(confidenceListFilt[camNum][mkr,:] > confidenceThreshold ,
                                                 np.isnan(confidenceListFilt[camNum][mkr,:])))
            if len(usedInds) > 0:
                ax.plot(usedInds,keypointListFilt[camNum][mkr,usedInds,mkrXY],linewidth=1)
                ax.set_ylim((.9*np.min(keypointListFilt[camNum][mkr,usedInds,mkrXY]),1.1*np.max(keypointListFilt[camNum][mkr,usedInds,mkrXY])))
            else:
                ax.text(0.5,0.5,'no data used',horizontalalignment='center',transform=ax.transAxes)
            
        plt.tight_layout()
        ax.legend(['unfilt','occlusionRemoved','filt','used for triang'],bbox_to_anchor=(1.05,1))
        
    # We need to add back the cameras that have been kicked out.
    # We just add back zeros, they will be kicked out of the triangulation.
    idxCameras2NotUse = [cameras2Use.index(cam) for cam in cameras2NotUse]
    for idxCamera2NotUse in idxCameras2NotUse:
        keypointsSync.insert(idxCamera2NotUse, np.zeros(keypointsSync[0].shape))
        confidenceSync.insert(idxCamera2NotUse, np.zeros(confidenceSync[0].shape))
        nansInOutSync.insert(idxCamera2NotUse, np.array([np.nan, np.nan]))
        startEndFrames.insert(idxCamera2NotUse, None)
 
    return keypointsSync, confidenceSync, nansInOutSync, startEndFrames