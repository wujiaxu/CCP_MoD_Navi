import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import argparse

import helpers as he
from cl_map import CLCellType
from cl_map import CLMap as cl

# line format
# time [ms] (unixtime + milliseconds/1000), person id, position x [mm], position y [mm], position z (height) [mm], velocity [mm/s], angle of motion [rad], facing angle [rad]
# time, person_id, x, y, z, velocity, motion_angle, facing_angle
if __name__ == '__main__':
    parser = argparse.ArgumentParser('Parse start goal condition')
    parser.add_argument('--start', type=int, default=4)
    parser.add_argument('--goal', type=int, default=2)
    args = parser.parse_args()
    file_name = "C:\\Users\\79359\\Downloads\\atc-20121114.csv"
    start_goal_data_with_labels = np.genfromtxt("start_goal_with_label.csv",
                                                delimiter=",")
    target_ped_id_list = start_goal_data_with_labels[
                            np.logical_and(
                                start_goal_data_with_labels[:,7]==args.start,
                                start_goal_data_with_labels[:,8]==args.goal),
                            0].tolist()

    chunksize = 500 ** 2
    loop_number = 0
    refresh_ratio = 10
    x_min = -50
    x_max = 10
    y_min = -12
    y_max = 24
    step = 1.
    p_shape = (round((y_max - y_min) / step), round((x_max - x_min) / step))

    cl_map = cl()

    cl_map.set_up_map(step=step, processing=CLCellType.STREAM)

    fig0, ax0 = plt.subplots(1, 1)  # ,sharex=True,sharey=True)
    # fig1, ax1= plt.subplots(1, 1)#,sharex=True,sharey=True)
    header=["time","person_id", "x","y","z",'velocity', 'motion_angle',"facing_angle"]

    for chunk in pd.read_csv(file_name, chunksize=chunksize):
        chunk.columns=header
        chunk = chunk.loc[chunk["person_id"].isin(target_ped_id_list)]
        # filter by ped_id with specific start and goal
        cl_map.load_data(chunk)
        loop_number = loop_number + 1
        plot_data = []
        mod_data = []
        if loop_number % refresh_ratio == 0:
            ax0.clear()
            ax0.set_aspect('equal')
            ax0.set_xlim(x_min, x_max)
            ax0.set_ylim(y_min, y_max)
            cl_map.cluster_data()

            p_array_vis = np.zeros(p_shape)
            #plot_angle_grid = np.zeros(p_shape)
            # visualisation
            for cell in cl_map.cells_data:
                for m,cov,w in zip(cell.clustering_results.mean_values,
                                 cell.clustering_results.covariances,
                                 cell.clustering_results.mixing_factors):
                    try:
                        u, v = he.pol2cart(m[0], m[1])
                        mod_data_row = [int((cell.corner[1] - y_min) / step), 
                                        int((cell.corner[0] - x_min) / step), 
                                        round(w,3),
                                        round(m[0],3), 
                                        round(m[1],3),
                                        round(cov[0,0],3),
                                        round(cov[0,1],3),
                                        round(cov[1,0],3),
                                        round(cov[1,1],3)]
                        row = [cell.corner[0] + cl_map.grid_step / 2, 
                               cell.corner[1] + cl_map.grid_step / 2, 
                               u, 
                               v]
                        plot_data.append(row)
                        mod_data.append(mod_data_row)
                        p_array_vis[int((cell.corner[1] - y_min) / step), 
                                    int((cell.corner[0] - x_min) / step)] = cell.count[0] / cl_map.total_number_of_observations
                        # plot_angle_grid[int((cell.corner[1] - y_min) / step), 
                        #             int((cell.corner[0] - x_min) / step)] = np.arctan2(v,u)*180./np.pi+180.
                    except:
                        pass
                        #print(p_shape, int((cell.corner[1] - y_min) / step),int((cell.corner[0] - x_min) / step))
            plot_data = np.array(plot_data)
            if len(mod_data)>0:
                mod_data = np.array(mod_data)
                print("shape:",mod_data.shape)
                # plot_angle_grid = np.where(p_array_vis>0,plot_angle_grid,-1)
                np.savetxt("mod_cliff_{}_{}.csv".format(args.start,args.goal),
                        mod_data,delimiter=",")
                obstacle = np.array([[-30000.,-22000,-21500.,-7000.,-7000.,2000.,8500.,5000.],
                            [900,500.,8500.,8500.,140.,0.,3300.,-1000.]])/1000.
                ax0.quiver(plot_data[:, 0], plot_data[:, 1], plot_data[:, 2], plot_data[:, 3], units='xy')
                ax0.scatter(obstacle[0],
                            obstacle[1],marker="*",c="b")
                ax0.set_title("Observations count: " + str(chunksize * loop_number))
                plt.savefig("result/directions_{}_{}_".format(args.start,args.goal) + str(loop_number).zfill(5) + '.png', bbox_inches='tight')
                # plt.show()

            # ax0.clear()
            # ax0.set_aspect('equal')
            # ax0.set_title("Observations count: " + str(chunksize * loop_number))
            # ax0.imshow(np.flipud(p_array_vis), cmap="plasma", vmin=0,vmax=np.max(np.max(p_array_vis)))
            # plt.savefig("result/intensity_" + str(loop_number).zfill(5) + '.png', bbox_inches='tight')
            # plt.show()