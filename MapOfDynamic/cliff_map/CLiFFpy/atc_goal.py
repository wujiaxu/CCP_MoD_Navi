import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from tqdm import tqdm

class Human:
    def __init__(self, id, traj_obs):

        self.id = id
        self.traj_obs = traj_obs[['time','x','y']].to_numpy()

        return 
    
    def add_traj(self, traj_obs):

        self.traj_obs = \
            np.concatenate(
                [self.traj_obs,
                traj_obs[['time','x','y']].to_numpy()],
                axis=0)

        return 
    
    def get_start_goal(self):

        start_time = self.traj_obs[0,0]
        start_pos = self.traj_obs[0,1:]
        end_time = self.traj_obs[-1,0]
        end_pos = self.traj_obs[-1,1:]

        return  start_time, start_pos, end_time, end_pos
    

if __name__ == "__main__":

    header=["time","person_id", "x","y","z",'velocity', 'motion_angle',"facing_angle"]
    file_name = "C:\\Users\\79359\\Downloads\\atc-20121114.csv"
    chunksize = 10000
    fig0, ax0 = plt.subplots(1, 1) 
    humans = {}
    start_goal_data = []
    x_min = -50000
    x_max = 10000
    y_min = -12000
    y_max = 24000
    for chunk in tqdm(pd.read_csv(file_name, chunksize=chunksize)):
        chunk.columns=header
        chunk = chunk.loc[chunk["x"]<x_max]
        chunk = chunk.loc[chunk["y"]<y_max]
        human_id_observed = chunk["person_id"].unique()
        #print(human_id_observed)

        # assume all previous human obs ended at first
        human_id_ended = list(humans.keys())
        
        # add obs to data buffer 
        for id in human_id_observed:
            if id in humans:
                humans[id].add_traj(chunk.loc[chunk["person_id"]==id])
                human_id_ended.remove(id)
            else:
                humans[id] = Human(id,chunk.loc[chunk["person_id"]==id])

        # release ended data from buffer 
        for id in human_id_ended:
            start_time, \
                start_pos, \
                end_time, \
                end_pos = humans[id].get_start_goal()
            start_goal_data.append(
                                [id, start_time, 
                                 start_pos[0], 
                                 start_pos[1],
                                 end_time, 
                                 end_pos[0],
                                 end_pos[1]]
                                )
            del humans[id]
            
        
    # save to csv
    start_goal_data = np.array(start_goal_data)
    np.savetxt("start_goal.csv",start_goal_data,delimiter=",", fmt='%f')
    ax0.set_aspect('equal')
    ax0.scatter(start_goal_data[:,2],start_goal_data[:,3],c="r")
    ax0.scatter(start_goal_data[:,5],start_goal_data[:,6],c="b")
    plt.show()
    plt.close()
    plt.clf()