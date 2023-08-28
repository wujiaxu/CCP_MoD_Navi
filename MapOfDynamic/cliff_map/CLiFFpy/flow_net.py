import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.patches as patches
from sklearn.cluster import DBSCAN

# start goal region in x,y,w,h
REGION_UP_LEFT = [-25,5,7,20]
REGION_UP_MID = [-18,5,15,20]
REGION_UP_RIGHT = [-3,3,15,10]
REGION_LEFT = [-42,-10, 15,15]
REGION_RIGHT = [5,-10,5,10]
REGION_BOT = [-25,-15,20,10]
REGION_LIST = [REGION_UP_LEFT,
               REGION_UP_MID,
               REGION_UP_RIGHT,
               REGION_LEFT,
               REGION_RIGHT,
               REGION_BOT]

def plot_cluster(ax,X_train,cluster_pred):

    for i in range(max(cluster_pred)+1):
        x = X_train[cluster_pred==i]
        ax.scatter(x[:,0], x[:,1], s=10, label=i,alpha=0.3)
        # ax.legend()
    

    return 

def clustering_start_goal(start_goal_data):

    start_pos = start_goal_data[:,2:4]/1000.
    end_pos = start_goal_data[:,5:7]/1000.
    dbscan = DBSCAN(eps=1, min_samples=40)
    cluster_pred_start = dbscan.fit_predict(start_pos)
    cluster_pred_end = dbscan.fit_predict(end_pos)

    return start_pos, end_pos, cluster_pred_start, cluster_pred_end

def manual_labeling_start_goal_region(start_goal_data):
    
    start_goal_region_labels = []
    for i in range(start_goal_data.shape[0]):
        start_pos = start_goal_data[i,2:4]/1000.
        end_pos = start_goal_data[i,5:7]/1000.
        region_label = []
        in_region = False
        for region_id, region in enumerate(REGION_LIST):
            in_region = in_box(start_pos, region)
            if in_region:
                region_label.append(region_id)
                break
        if not in_region:
            region_label.append(-1)
        in_region = False
        for region_id, region in enumerate(REGION_LIST):
            in_region = in_box(end_pos, region)
            if in_region:
                region_label.append(region_id)
                break
        if not in_region:
            region_label.append(-1)
        start_goal_region_labels.append(region_label)

    start_goal_region_labels = np.array(start_goal_region_labels)
    start_goal_data_with_labels = np.concatenate([start_goal_data,
                                                  start_goal_region_labels],
                                                  axis=1)

    return start_goal_data_with_labels

def in_box(point, xywh):
    if point[0]<xywh[0] or point[0]>xywh[0]+xywh[2]:
        return False
    if point[1]<xywh[1] or point[1]>xywh[1]+xywh[3]:
        return False
    return True

def plot_box(ax,xywh):

    r = patches.Rectangle(xy=(xywh[0], xywh[1]), 
                          width=xywh[2],
                            height=xywh[3], 
                            ec='#000000', fill=False)
    ax.add_patch(r)
    return

def adjecent_matrix_flow_net(source_sink_label):
    max_id = int(np.max(source_sink_label))

    ad_matrix = np.zeros((max_id+1,max_id+1))

    for i in range(source_sink_label.shape[0]):
        source = int(source_sink_label[i,0])
        sink = int(source_sink_label[i,1])
        if source > -1 and sink > -1:
            ad_matrix[source,sink] = ad_matrix[source,sink] + 1
    return ad_matrix
if __name__ == "__main__":
    fig, ax = plt.subplots()
    start_goal_data = np.genfromtxt("start_goal.csv",delimiter=",")
    
    # start_pos, end_pos, \
    #     cluster_pred_start, cluster_pred_end = clustering_start_goal(start_goal_data)
    # plot_cluster(ax,start_pos,cluster_pred_start)
    # plot_cluster(ax,end_pos,cluster_pred_end)
    # for region in REGION_LIST:
    #     plot_box(ax,region)
    start_goal_data_with_labels = manual_labeling_start_goal_region(start_goal_data)
    np.savetxt("start_goal_with_label.csv",
               start_goal_data_with_labels,
               delimiter=",",fmt='%f')
    ad_matrix = adjecent_matrix_flow_net(start_goal_data_with_labels[:,7:9])
    ax.imshow(ad_matrix)
    plt.show()
    plt.close()
    plt.clf()