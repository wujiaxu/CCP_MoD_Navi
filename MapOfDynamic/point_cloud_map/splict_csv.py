import pandas as pd
import lzma
source_path = "C:\\Users\\79359\\Downloads\\atc-20121114.csv"
"""
time [ms] (unixtime + milliseconds/1000), person id, position x [mm], position y [mm], position z (height) [mm], velocity [mm/s], angle of motion [rad], facing angle [rad]
"""
# with lzma.open(source_path, "r") as f:
for i,chunk in enumerate(pd.read_csv(source_path, chunksize=200000)):
    print('start writing to raw_data/atc/traj_data/atc-20121114_{}.csv'.format(i))
    chunk.to_csv('raw_data/atc/traj_data/atc-20121114_{}.csv'.format(i), index=False,header=["time [ms]","ped_id", "x [mm]","y [mm]","z [mm]","v [mm/s]","rz [rad]","facing angle [rad]"])