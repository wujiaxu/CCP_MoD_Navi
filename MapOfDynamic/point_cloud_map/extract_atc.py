'''
Example code for reading raw 3D range sensor data from the ATC sample dataset
(see: http://www.irc.atr.jp/crest2010_HRI/ATC_dataset/)  

Copyright (c) 2013, 2023 ATR

UPDATE 2023: Python version, with conversion to 3D points
'''

import os
import struct
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

'''
Format of files: the files contain a sequence of "frames".
Each frame corresponds to a single measurement and has the following format:
 _________________________________________________________________________________________________________
 | header marker |  version  |  unixtime[s] |  time[ms]  | reserved |  data length  ||        data       |
 +---------------+-----------+--------------+------------+----------+---------------++-------------------+
 |      '+'      |   '003'   |    10 byte   |   3 byte   |  10byte  |  5 byte(hex)  ||  2 byte * length  |
 ---------------------------------------------------------------------------------------------------------
 
 The data is stored as 16-bit integers (short) in binary format 

'''

class SensorInfo:
    pos_x = 0.0 # mm
    pos_y = 0.0
    pos_z = 0.0
    rot_x = 0.0 # rad
    rot_y = 0.0
    rot_z = 0.0
    hor_min_angle = 0.0 
    hor_max_angle = 0.0
    hor_resolution = 0.0
    ver_min_angle = 0.0
    ver_max_angle = 0.0
    ver_resolution = 0.0
    radial_distortion = 0.0
    sensor_type = ""
    range_correction_factor = 0.0
    



class RangeDataConverter:
    def __init__(self, sensor_info, sensor_type="D-IMager"):
        self.sensor_info = sensor_info
        
        self.transformFactors = np.zeros((self.sensor_info.hor_resolution*self.sensor_info.ver_resolution,3))
        
        self.sensor_info.sensor_type = sensor_type
            
        if sensor_type=="DImager":
            self.sensor_info.radial_distortion = -2.23197e-5
        
        # precalculate transformation factors 
        if sensor_type=="Velodyne":
            self.precalculateTransformationRotatingScanner()
        else:
            self.precalculateTransformationPinhole()
        
    def precalculateTransformationPinhole(self):
        # calculate rotation matrix
        rotMat = np.zeros((3,3))
        
        # Tait-Bryan angles or Euler angle sequence (1,2,3) (technically Cardan angles though as no repetition):
        #
        # self.sensor_info.rot_z := self.sensor_info.rot_z, yaw, first intrinsic rotation, around local z axis      [-pi, +pi]
        # theta := self.sensor_info.rot_y, pitch (or tilt), second intrinsic rotation, around local y axis [-pi/2, +pi/2]
        # phi := self.sensor_info.rot_x, roll, third intrinsic rotation, around local x axis     [-pi, +pi]
        #  
        rotMat[0,0] = np.cos(self.sensor_info.rot_y) * np.cos(self.sensor_info.rot_z);
        rotMat[0,1] = np.cos(self.sensor_info.rot_y) * np.sin(self.sensor_info.rot_z);
        rotMat[0,2] = -np.sin(self.sensor_info.rot_y);
        rotMat[1,0] = np.sin(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_y) * np.cos(self.sensor_info.rot_z) - np.cos(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_z);
        rotMat[1,1] = np.sin(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_y) * np.sin(self.sensor_info.rot_z) + np.cos(self.sensor_info.rot_x) * np.cos(self.sensor_info.rot_z);
        rotMat[1,2] = np.cos(self.sensor_info.rot_y) * np.sin(self.sensor_info.rot_x);
        rotMat[2,0] = np.cos(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_y) * np.cos(self.sensor_info.rot_z) + np.sin(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_z);
        rotMat[2,1] = np.cos(self.sensor_info.rot_x) * np.sin(self.sensor_info.rot_y) * np.sin(self.sensor_info.rot_z) - np.sin(self.sensor_info.rot_x) * np.cos(self.sensor_info.rot_z);
        rotMat[2,2] = np.cos(self.sensor_info.rot_y) * np.cos(self.sensor_info.rot_x);
        
        # sensor focal length (using info for horizontal - vertical focal length assumed to be the same)
        focus = self.sensor_info.hor_resolution / 2 / np.tan((self.sensor_info.hor_max_angle - self.sensor_info.hor_min_angle) / 2)
        
        # correction due to radial distortion
        focus = focus / (1 + self.sensor_info.radial_distortion * self.sensor_info.hor_resolution * self.sensor_info.hor_resolution / 4);
        
        # precalculate transormation factors for all pixels
        for index in range(self.sensor_info.hor_resolution*self.sensor_info.ver_resolution):
        
            # x, y coordinate in image
            indV = self.sensor_info.ver_resolution // 2 - index // self.sensor_info.hor_resolution; 
            indH = index % self.sensor_info.hor_resolution - self.sensor_info.hor_resolution // 2 + 1;
            
            delta = (1 + self.sensor_info.radial_distortion * (indV * indV + indH * indH));
            
            vector_c = np.zeros((3,1))
            vector_c[2] = focus * delta / np.sqrt(focus * focus * delta * delta + indV * indV + indH * indH)
            vector_c[1] = vector_c[2] * indH / focus / delta
            vector_c[0] = vector_c[2] * indV / focus / delta
            
            # transfomr and rotate 180 deg around y axis 
            self.transformFactors[index,:] = rotMat.T.dot(vector_c).T*np.array((-1,1,-1))
            

    def precalculateTransformationRotatingScanner(self):     
        # precalculate transormation factors for all pixels
        for index in range(self.sensor_info.hor_resolution*self.sensor_info.ver_resolution):
            # x, y coordinate in image (starting from 0,0)
            indV = int(index // self.sensor_info.hor_resolution) # index of vertical angle
            indH = index - indV * self.sensor_info.hor_resolution # index of horizontal angle

            hor_sample_step = (self.sensor_info.hor_max_angle - self.sensor_info.hor_min_angle) / self.sensor_info.hor_resolution
            ver_sample_step = (self.sensor_info.ver_max_angle - self.sensor_info.ver_min_angle) / self.sensor_info.ver_resolution
        
            # angles of the lasers
            deltaYRot = self.sensor_info.ver_max_angle - indV * ver_sample_step
            # horizontal - rotation around x
            xRot = self.sensor_info.hor_max_angle - indH * hor_sample_step  + self.sensor_info.rot_x
            # vertical - rotation around y
            yRot = self.sensor_info.rot_y
            # heading of the sensor - rotation around z
            zRot = self.sensor_info.rot_z

            # calculate position - deltaY-Z-Y-X rotation of vector [0 0 -range] (with negative rotation around Y axis)
            # [the zero-th position of the sensor is facing straight down]
            # helper variable cxsy
            temp = np.cos(xRot) * np.sin(yRot)
            # x = x_sensor + range * (sDcycz + cD(-sxsz+cxsycz))
            self.transformFactors[index,0] =  (np.sin(deltaYRot)*np.cos(yRot)*np.cos(zRot) + np.cos(deltaYRot) * ( - np.sin(xRot) * np.sin(zRot) + np.cos(zRot) * temp ) )
            # y = y_sensor + range * (sDcysz + cD(sxcz+cxsysz))
            self.transformFactors[index,1] =  (np.sin(deltaYRot)*np.cos(yRot)*np.sin(zRot) + np.cos(deltaYRot) * ( np.sin(xRot) * np.cos(zRot) + np.sin(zRot) * temp ) )
            # z = z_sensor + range * (sDsy - cDcxcy)
            self.transformFactors[index,2] =  (np.sin(deltaYRot)*np.sin(yRot) - np.cos(deltaYRot)*np.cos(xRot) * np.cos(yRot))            


    # convert range data to 3d points
    def rangeToWorldCoordinates(self, rangeArray):        
        return np.asarray((self.sensor_info.pos_x, self.sensor_info.pos_y, self.sensor_info.pos_z)) + (self.transformFactors.T*rangeArray).T


    # correcting range data based on approximate heuristics 
    def correctRangeData(self, datain):

        # Panasonic sensor range correction heuristic
        if self.sensor_info.sensor_type == "D-IMager":
            correctedRangeDataBuf = np.zeros((datain.size))
            indices = datain < 3200
            correctedRangeDataBuf[indices] = datain[indices] - datain[indices]*120/3200
            indices = (datain >= 3200) & (datain < 4750)
            correctedRangeDataBuf[indices] = datain[indices] - (120 - (datain[indices]-3200)*30/1550)
            indices = (datain >= 4750) & (datain < 6500)
            correctedRangeDataBuf[indices] = datain[indices] - (30 + (datain[indices]-4750)*350/1750);
            indices = datain >= 6500
            correctedRangeDataBuf[indices] = datain[indices] - (350 - (datain[indices]-6500)*150/1500);
            
        else:
            correctedRangeDataBuf = datain;
    
        # range correction
        if self.sensor_info.range_correction_factor != 0.0:
            #correctedRangeDataBuf[correctedRangeDataBuf>3000] += self.sensor_info.range_correction_factor/100.0 * (correctedRangeDataBuf[correctedRangeDataBuf>3000] - 3000)
            correctedRangeDataBuf[correctedRangeDataBuf>3000] = np.add(correctedRangeDataBuf[correctedRangeDataBuf>3000], 
                                                                       self.sensor_info.range_correction_factor/100.0 * (correctedRangeDataBuf[correctedRangeDataBuf>3000] - 3000), 
                                                                       out=correctedRangeDataBuf[correctedRangeDataBuf>3000], casting="unsafe")
        return correctedRangeDataBuf;



def readOneFrame(op):
    header_marker = op.read(1).decode()
    if header_marker == "":
        return [] 
    assert(header_marker == "+")
    version = op.read(3)
    unixtime = op.read(10)
    time = op.read(3)
    reserved = op.read(10)
    data_length = int(op.read(5).decode(), 16)

    # read data as list
    data_list = []
    for i in range(data_length):
        item = op.read(2)
        num = struct.unpack("h", item)[0]
        data_list.append(num)
    return data_list,time

def readSensorInfo(calib_file:str):

    sensor_info_dict = {}

    df = pd.read_excel(calib_file,header=1,index_col ="ID")
    
    for sensor_name in df.index.to_list()[:49]:
        sensor_info = SensorInfo()
        sensor_raw = df.loc[sensor_name]
        
        sensor_info.pos_x = sensor_raw.loc["x [mm]"]
        sensor_info.pos_y = sensor_raw.loc["y [mm]"]
        sensor_info.pos_z = sensor_raw.loc["z [mm]"]
        sensor_info.rot_x = np.deg2rad(sensor_raw.loc["phi_x [deg]"])
        sensor_info.rot_y = np.deg2rad(sensor_raw.loc["phi_y [deg]"])
        sensor_info.rot_z = np.deg2rad(sensor_raw.loc["phi_z [deg]"])
        sensor_info.hor_min_angle = np.deg2rad(sensor_raw.loc["min. angle"])
        sensor_info.hor_max_angle = np.deg2rad(sensor_raw.loc["max. angle"])
        sensor_info.hor_resolution = int(sensor_raw.loc["resolution"])
        sensor_info.ver_min_angle = np.deg2rad(sensor_raw.loc["min. angle.1"])
        sensor_info.ver_max_angle = np.deg2rad(sensor_raw.loc["max. angle.1"])
        sensor_info.ver_resolution = int(sensor_raw.loc["resolution.1"])
        sensor_info.range_correction_factor = sensor_raw.loc["range correction factor"]
        sensor_info.sensor_type = sensor_raw.loc["Type"]

        sensor_info_dict[sensor_name] = sensor_info
    return sensor_info_dict


def extract_map():



    return

def extract_sub_map_stream(sensor_name, data_file):
    # plot3d=True

    # plt.ion()

    # # prepare figure for plotting
    # fig = plt.figure()
    # #ax = fig.add_subplot(projection='3d')
    # ax = fig.add_subplot()
    # with open(data_path_v1, 'rb') as op_v1, open(data_path_v2, 'rb') as op_v2:
    #     # loop
    #     # for i in range(60):
    #     while True:
            
    #         # read on frame as list
    #         data_list_v1,time = readOneFrame(op_v1)
    #         data_list_v2,_ = readOneFrame(op_v2)
            
    #         # convert list to numpy array
    #         data_np_v1=np.asarray(data_list_v1)
    #         data_np_v2=np.asarray(data_list_v2)
            
    #         # correct data ranges
    #         data_np_v1 = data_converter_v1.correctRangeData(data_np_v1)
    #         data_np_v2 = data_converter_v2.correctRangeData(data_np_v2)

    #         # convert data to 3d pointcloud
    #         data3d_v1 = data_converter_v1.rangeToWorldCoordinates(data_np_v1)
    #         data3d_v2 = data_converter_v2.rangeToWorldCoordinates(data_np_v2)

    #         data3d = np.concatenate([data3d_v1,data3d_v2],axis=0)
    #         data3d = data3d[data3d[:,2]>1000]
    #         data3d = data3d[data3d[:,2]<2000]
    #         if plot3d:
    #             # plot pointcloud
    #             ax.clear()
    #             ax.scatter(data3d[:,0], data3d[:,1], marker='.', s=3,alpha=0.3)
    #             #ax.hist(data3d[:,2],100)
    #             #ax.scatter(data3d[:,0], data3d[:,1], data3d[:,2], marker='.', s=3,alpha=0.3)
    #         else:
    #             # plot range image
    #             range_image=np.reshape(data_list_v1,(sensor_info_v1.ver_resolution,sensor_info_v1.hor_resolution))
    #             plt.clf()
    #             plt.imshow(range_image)
    #         plt.title(str(time))
    #         plt.show()
    #         plt.pause(.001)
    return 

# below - test code

if __name__ == "__main__":
    extract_map()

    sensor_info_dict = readSensorInfo("raw_data/atc/atc-sensors.xlsx")
    data_converter_dict = {}
    data_path_dict = {}
    for sensor_name in sensor_info_dict:
        sensor_info = sensor_info_dict[sensor_name]
        data_converter_dict[sensor_name] = RangeDataConverter(sensor_info, sensor_type=sensor_info.sensor_type)
        data_path = "raw_data/atc/pc_data/"+sensor_name+"/"
        data_files = os.listdir(data_path)
        data_path = data_path + data_files[10]
        data_path_dict[sensor_name] = data_path

    #plt.ion()

    # prepare figure for plotting
    fig = plt.figure()
    #ax = fig.add_subplot(projection='3d')
    ax = fig.add_subplot()

    data3d = []
    for sensor_name in sensor_info_dict:
        print(sensor_name)
        sensor_info = sensor_info_dict[sensor_name]
        data_converter = data_converter_dict[sensor_name]
        data_path = data_path_dict[sensor_name]
        try:
            with open(data_path, 'rb') as op:
                # read on frame as list
                data_list,time = readOneFrame(op)
                
                # convert list to numpy array
                data_np=np.asarray(data_list)
                
                # correct data ranges
                data_np = data_converter.correctRangeData(data_np)

                # convert data to 3d pointcloud
                data3d_sub = data_converter.rangeToWorldCoordinates(data_np)

                data3d.append(data3d_sub)
        except Exception as e:
            print(e)

    data3d = np.concatenate(data3d,axis=0)
    data3d = data3d[data3d[:,2]>1500]
    data3d = data3d[data3d[:,2]<5000] 
    # np.savetxt("map_{}.csv".format(time),data3d,delimiter=",")
    
    # plot pointcloud
    ax.clear()
    ax.scatter(data3d[:,0], data3d[:,1], marker='.', s=3,alpha=0.3)
    #ax.hist(data3d[:,2],100)
    #ax.scatter(data3d[:,0], data3d[:,1], data3d[:,2], marker='.', s=3,alpha=0.3)
    
    plt.title(str(time))
    plt.grid()
    plt.show()
    #plt.pause(.001)