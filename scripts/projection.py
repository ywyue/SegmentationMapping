import sys,os, pdb
import numpy as np
import tensorflow as tf
import cv2

import rospy, pdb

from label2color import  background, label_to_color
from helper import get_cropped_uv_rotated, is_out_of_bound, is_out_of_bound_rotated, softmax

class LidarSeg:
    def __init__(self, neural_net_graph_path, is_output_distribution, num_output_class):
        # read the network
        with tf.gfile.GFile(neural_net_graph_path, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
        
        # tf configs
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.sess = tf.Session(config=config)

        # the input and output of the neural net
        self.y, = tf.import_graph_def(graph_def, return_elements=['network/output/ArgMax:0'])
        self.G = tf.get_default_graph()
        self.x = self.G.get_tensor_by_name('import/network/input/Placeholder:0')
        self.is_train = self.G.get_tensor_by_name('import/network/input/Placeholder_2:0')
        self.is_output_distribution = is_output_distribution
        if self.is_output_distribution:
            self.distribution = self.G.get_tensor_by_name('import/network/upscore_8s/upscore8/upscore8/BiasAdd:0')
        self.num_output_class = num_output_class

        # initialization
        tf.global_variables_initializer().run(session=self.sess)

        self.intrinsic = []
        self.cam2lidar = []
        self.distort_map = []
        self.counter = 0

    def add_cam(self,intrinsic_mat, cam2lidar, distort):
        """
        param: intrinsic_mat: 3x4 
               extrinsic_mat: 4x4, 
        """
        self.intrinsic.append(intrinsic_mat)
        self.cam2lidar.append( cam2lidar )
        self.distort_map.append(distort)

        

    def project_lidar_to_seg(self, lidar, rgb_img, camera_ind, camera_shape, is_output_distribution, original_img):
        """
        assume the lidar points can all be projected to this img
        assume the rgb img shape meets the requirement of the neural net input

        lidar points: 3xN
        """
        if is_output_distribution:
            out, distribution = self.sess.run([self.y, self.distribution],
                                              feed_dict={self.x: np.expand_dims(rgb_img,axis=0),
                                                         self.is_train: False})
            out = out [0,:,:]
            #background_sum = np.sum(distribution[0, :, :, self.num_output_class:], axis=2) + distribution[0, :, :, 0]
            #distribution = distribution[0, :, :, :self.num_output_class]
            distribution = distribution[0, :, :, :self.num_output_class]
            #distribution[:, :, 0] = background_sum
        else:
            out = self.sess.run(self.y,
                                feed_dict={self.x: np.expand_dims(rgb_img,axis=0),
                                           self.is_train: False})
            distribution = []
            out = out [0,:,:]
        

        # project lidar points into camera coordinates
        T_c2l = self.cam2lidar[camera_ind][:3, :]
        lidar_in_cam = np.matmul(self.intrinsic[camera_ind], T_c2l )
        projected_lidar_2d = np.matmul( lidar_in_cam, lidar)
        projected_lidar_2d[0, :] = projected_lidar_2d[0, :] / projected_lidar_2d[2, :]
        projected_lidar_2d[1, :] = projected_lidar_2d[1, :] / projected_lidar_2d[2, :]
        print("total number of lidar : "+str(projected_lidar_2d.shape))
        #projected_lidar_2d[2, :] = 1
        idx_infront = projected_lidar_2d[2, :]>0
        x_im = projected_lidar_2d[0, :][idx_infront]
        y_im = projected_lidar_2d[1, :][idx_infront]
        z_im = projected_lidar_2d[2, :][idx_infront]
        points_on_img = np.zeros((3, x_im.size))
        points_on_img[0, :] = x_im
        points_on_img[1, :] = y_im
        points_on_img[2, :] = z_im
        # distort the lidar points based on the distortion map file
        projected_lidar_2d = self.distort_map[camera_ind].distort(points_on_img)

        
        # for debug use: visualize the projection on the original rgb image
        #for col in range(projected_lidar_2d.shape[1]):
        #    u = int(round(projected_lidar_2d[0, col] , 0))
        #    v = int(round(projected_lidar_2d[1, col] , 0))
        #    cv2.circle(original_img, (u, v),2, (0,0,255))
        #cv2.imwrite("original_project"+str(self.counter)+".png", original_img)
        #cv2.imshow("original projection", original_img)
        #cv2.waitKey(100)
        #print("write projection")
        
        
        projected_points = []
        projected_index  = []
        labels = []
	original_rgb = []
        class_distribution = []
        for col in range(projected_lidar_2d.shape[1]):
            u, v, d = projected_lidar_2d[:, col]
            u ,v = get_cropped_uv_rotated(u, v)
            if is_out_of_bound(u, v):
                continue
            projected_points.append(lidar[:, col])
            label = out[int(v), int(u)] if out[v, u] < self.num_output_class else 0

            labels.append(label)
	    original_rgb.append(rgb_img[int(v), int(u)])
            projected_index.append(col)
            if self.is_output_distribution:
                distribution_normalized = softmax(distribution[int(v), int(u), :])
                class_distribution.append(distribution_normalized)
                
        self.visualization(labels, projected_index, projected_lidar_2d, rgb_img)
        return labels, projected_points, class_distribution, original_rgb
        

    def visualization(self, labels,index,  projected_points_2d, rgb_img):
        to_show = rgb_img
        print("num of projected lidar points is "+str(len(labels)))
        for i in range(len(labels )):
            p = (int(projected_points_2d[0, index[i]]),
                 int(projected_points_2d[1, index[i]]))
            #cv2.putText(to_show,. str(int(labels[i])), 
            #            p,
            #            cv2.FONT_HERSHEY_SIMPLEX, 5, (0,0,203))
            #if is_out_of_bound(p[0], p[1]): continue
            
            if labels[i] in label_to_color:
                color = label_to_color[labels[i]]
            else:
                color = label_to_color[background]

            cv2.circle(to_show,get_cropped_uv_rotated(p[0], p[1]),2, color)
        #cv2.imwrite("projected"+str(self.counter)+".png", to_show)
        self.counter +=1
        #cv2.imshow("projected",to_show)
    #cv2.waitKey(100)

        


    
    
