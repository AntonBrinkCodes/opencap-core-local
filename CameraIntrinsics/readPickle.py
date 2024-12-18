
import pandas as pd
filepath = 'CameraIntrinsics/iPad8,9/Deployed_720_60fps/cameraIntrinsics.pickle'
obj = pd.read_pickle(filepath)
print(obj)