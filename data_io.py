
"""
INFOS:
coordinates (on maps): (latitude, longitude) / (breitengrad, laengengrad)
latitude in [-90, 90] not periodically continued, longitude in [-180, 180] periodically continued
bot in units of (fractional) degrees (NOT: minute/second)
"""


import os
import shutil
import csv
import math
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
import matplotlib.pyplot as plt
from datetime import datetime
from tqdm import tqdm


###################################################################
# INITIAL DATA SETUP ROUTINES
###################################################################


def copy_useful_data_to_workspace(tmp_data_path: str, workspace_data_path: str):
    dir_list = os.listdir(tmp_data_path)
    useful_dir_counter = 0
    for dir in dir_list:
        if "labels.txt" in os.listdir(tmp_data_path + dir):
            useful_dir_counter += 1
            os.mkdir(workspace_data_path + dir)
            shutil.copy(tmp_data_path + dir + "/labels.txt", workspace_data_path + dir + "/labels.txt")
            os.mkdir(workspace_data_path + dir + "/Trajectory")
            for trajectory in os.listdir(tmp_data_path + dir + "/Trajectory"):
                shutil.copy(tmp_data_path + dir + "/Trajectory/" + trajectory,
                            workspace_data_path + dir + "/Trajectory/" + trajectory)

    print("Number of useful directories: {} (of {})".format(useful_dir_counter, len(dir_list)))


def read_trajectory(trajectory_path: str):

    timestamps = []
    longitudes = []     # laengengrad in grad
    latitudes = []      # breitengrad in grad
    altitudes = []      # hoehe in feet ?!


    with open(trajectory_path, "r") as file:
        reader = csv.reader(file, delimiter=",")

        for counter, row in enumerate(reader):
            # skip first 6 rows:
            if counter <= 5:
                continue

            # get timestamp:
            date = row[5].split("-")
            time = row[6].split(":")
            dt = datetime(int(date[0]), int(date[1]), int(date[2]), int(time[0]), int(time[1]), int(time[2]))
            timestamps.append(dt.timestamp())

            # get (3D) coordinates:
            latitudes.append(float(row[0]))
            longitudes.append(float(row[1]))
            altitudes.append(float(row[3]))

    return timestamps, latitudes, longitudes, altitudes


def read_trajectory_labels(label_path: str):

    timestamps_start = []
    timestamps_end = []
    labels = []

    with open(label_path, "r") as file:
        reader = csv.reader(file, delimiter="\t")

        # skip header line:
        header = reader.__next__()

        for row in reader:
            # get start / end timestamp:
            for idx in range(2):
                d = row[idx].split(" ")[0]
                d = d.split("/")
                t = row[idx].split(" ")[1]
                t = t.split(":")
                dt = datetime(int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]), int(t[2]))
                if idx == 0:
                    timestamps_start.append(dt.timestamp())
                else:
                    timestamps_end.append(dt.timestamp())

            # get label:
            labels.append(row[2])

    return timestamps_start, timestamps_end, labels


def label_trajectories(target_directory: str):

    # read label file and initialize label index:
    labels_t_start, labels_t_end, labels_labels = read_trajectory_labels(target_directory + "/labels.txt")
    label_index = 0

    # get sorted trajectory filenames
    sorted_trajectory_names = os.listdir(target_directory + "/Trajectory")
    sorted_trajectory_names = sorted(sorted_trajectory_names, key=lambda x: int(x.split(".")[0]))

    # open file to write into:
    with open(target_directory + "/labeled_trajectories.csv", "w") as csv_file:
        writer = csv.writer(csv_file, delimiter="\t")

        # used for finishing function:
        finished_label_file = False

        # iterate through gps path files:
        for file_name in sorted_trajectory_names:

            if finished_label_file:
                break

            # get trajectory:
            times, latitudes, longitudes, altitudes = read_trajectory(target_directory + "/Trajectory/" + file_name)

            for t, lat, long, alt in zip(times, latitudes, longitudes, altitudes):

                # skip all labels of past times:
                try:
                    while labels_t_end[label_index] < t:
                        # divide different paths:
                        writer.writerow(["", "", "", "", ""])
                        label_index += 1
                # thrown if labels.txt reaches end:
                except IndexError:
                    finished_label_file = True
                    break

                # skip points below T_0:
                if t < labels_t_start[label_index]:
                    continue

                writer.writerow([t, lat, long, alt, labels_labels[label_index]])


def create_training_data_distance_time(target_directory: str):

    def reset_variables():
        return "", [], [], ""

    with open(target_directory + "/training_data.txt", "w") as out_file:
        writer = csv.writer(out_file, delimiter=";")

        with open(target_directory + "/labeled_trajectories.csv", "r") as csv_file:
            reader = csv.reader(csv_file, delimiter="\t")

            # init variables to store data:
            label, distances, times, row_tmp = reset_variables()

            # iterate through trajectory file:
            for row in tqdm(reader):

                # check for end of trajectory
                if row[0] == "":
                    # store trajectory and reset variables:
                    if label != "":
                        writer.writerow([label, times, distances])
                    label, distances, times, row_tmp = reset_variables()

                # add data if row is not empty:
                else:
                    # get label if not yet set:
                    if label == "":
                        label = row[4]

                    # add time difference:
                    if row_tmp != "":
                        times.append(int(float(row[0])-float(row_tmp[0])))

                    # add distance:
                    if row_tmp != "":
                        p1 = [float(row_tmp[1]), float(row_tmp[2])]
                        p2 = [float(row[1]), float(row[2])]
                        distances.append(int(gps_distance(p1, p2)+0.5))  # TODO: now in m as int

                    # store row for next step:
                    row_tmp = row


###################################################################
# DATA INVESTIGATION
###################################################################


def get_user_stats():
    user_path = "/home/julius/PycharmProjects/_shared_data/GPSLabels/trajectories/"
    for dir in sorted([dir for dir in os.listdir(user_path)], key=lambda dir: int(dir)):
        if dir == "010":
            continue
        data = read_training_data(user_path + dir + "/training_data.txt")
        lens = []
        ts = []
        tsteps = []
        for tup in data:
            lens.append(len(tup[0]))
            ts.append(np.sum(tup[0]))
            if len(tup[0]) > 0:
                tsteps.append(np.mean(tup[0]))
        if len(lens) > 0:
            out_str = "{}: Num tras: {}\t Mean tra len: {}\t Max tra len: {}\t mean time span: {}min\t max time span: {}min\t mean time step size: {}s"
            print(out_str.format(dir, len(data), int(np.mean(lens)), np.max(lens), int(np.mean(ts)/60), int(np.max(ts)/60), int(np.mean(tsteps))))
        else:
            print("{}: skipped".format(dir))


###################################################################
# VISUALIZATION
###################################################################


# TODO
def create_map_with_marker():
    # https://developers.google.com/maps/documentation
    # https://developers.google.com/maps/documentation/javascript/adding-a-google-map
    # https://www.geeksforgeeks.org/python-plotting-google-map-using-gmplot-package/
    # https://www.tutorialspoint.com/plotting-google-map-using-gmplot-package-in-python
    pass


###################################################################
# HELPER FUNCTIONS
###################################################################


def gps_distance(p1: list, p2: list):
    """
    @param p[1/2]:  Coordinate Point (latitude, longitude) in floating angular notation
    @return:        The Distance between the coordinate points [meter]

    """
    r_earth = 6371000    # earth radius in meter
    p1_rad = [math.radians(x) for x in p1]
    p2_rad = [math.radians(x) for x in p2]
    d_haversine = haversine_distances([p1_rad, p2_rad])
    d_real = d_haversine * r_earth
    return d_real[0][1]


def read_training_data(path: str):
    with open(path, "r") as file:
        reader = csv.reader(file, delimiter=";")
        data_tuples = []
        for row in reader:
            label = row[0]
            times = eval(row[1], {"__builtins__": None}, {})        # careful with eval (security)
            distances = eval(row[2], {"__builtins__": None}, {})    # careful with eval (security)
            data_tuples.append((times, distances, label))
    return data_tuples


###################################################################
# MAIN FUNCTIONS / ENTRY POINT
###################################################################


def main():
    # trajectory_path = "data/trajectories/010/Trajectory/20070804033032.plt"
    # _, _, _, _ = read_trajectory(trajectory_path)
    # label_path = "data/trajectories/010/labels.txt"
    # read_trajectory_labels(label_path)
    get_user_stats()


def main_create_training_data():
    data_path = "/home/julius/PycharmProjects/_shared_data/GPSLabels/trajectories/"
    for dir in os.listdir(data_path):
        create_training_data_distance_time(data_path + dir)


def main_label_data():
    dirs = ["/home/julius/PycharmProjects/_shared_data/GPSLabels/trajectories/" + directory for directory in
            os.listdir("/home/julius/PycharmProjects/_shared_data/GPSLabels/trajectories")]
    for directory in tqdm(dirs):
        label_trajectories(directory)


def main_data_import():
    tmp_data_path = "/home/julius/Downloads/Geolife Trajectories 1.3/Data/"
    workspace_data_path = "/home/julius/PycharmProjects/_shared_data/GPSLabels/trajectories/"
    copy_useful_data_to_workspace(tmp_data_path, workspace_data_path)


if __name__ == '__main__':
    main()

