# SegmentationMapping
* Label pointcloud from stereo cameras or lidar with Tensorflow trained neural nets graph.pb
* Build 3D Semantic voxel maps, 2D occupancy maps, 2D obstacle distance maps

## Pipeline

## Performance


## Dependencies
Neural Network: 
* `tensorflow-gpu-1.8.0` 
* `cuda-9.0`,
* `cudnn-7`

Python thirdparty: 
* [`python-pcl`](https://github.com/strawlab/python-pcl) 
* `python-opencv`

C++: `pcl`, `eigen`, `OpenCV`

ros thirdparty: 
* [`semantic octomap`](https://github.com/UMich-BipedLab/octomap.git): Modified octomap, supporting Bayesian updates for semantic label fusion
* [`ros_numpy`](https://github.com/eric-wieser/ros_numpy)

## launchfiles
* run on Cassie with stereo camera (Intel Realsense): `roslaunch SegmentationMapping cassie_stereo_py.launch`
* run nclt dataset: `roslaunch SegmentationMapping nclt_distribution_deeplab.launch`

<!---
# parameters in the launch file
*  `bagfile`: The path of the bag file
* `neural_net_graph_path`: The path of the neural network graph.pb file
* `is_output_distribution`: whether we need the distribution of all classes, or just the final label (the class with the max probability)
* `neural_net_input_width`: the width of the neural network input
* `neural_net_input_height`: the height of the neural network input
* `lidar`: the topic of lidar Pointcloud2
* `velodyne_synced_path`: for nclt, the pointcloud comes from synced files, instead of subcriptions from topics
* `camera_num`: the number of cameras
* `image_0`: the image topic of 0-th camera. Use `image_[0-9]` to indexing camera topics. There can be mulitple cameras
* `cam_intrinsic_0`: the `npy` file containing the intrinsic transformation of 0-th camera. Use `image_[0-9]` to indexing camera topics. Distortion is not taken into account
* `cam2lidar_file_0`: the `npy` file containing camera to lidar transformation of 0-th camera. Use `image_[0-9]` to indexing camera topics
* `cam_distortion_0`: the txt file contaning dense map from undistorted images to distorted images for this (0-th in the example) camera
--->

## On NCLT: Generate cam2lidar npy given measured transformation
`cd config/; python generate_cam2lidar.py`. Note that you have to hand-type in the `[x,y,z, roll, pitch, yawn]` in `generate_cam2lidar.py`


