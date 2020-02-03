
import os
import shutil
import csv
from datetime import datetime


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

    # print("Number of points in this trajectory: {}".format(len(timestamps)))

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

    # print("Number of labeled trajectories: {}".format(len(labels)))

    return timestamps_start, timestamps_end, labels


def label_trajectories(target_directory: str):
    # os.mkdir(target_directory + "/labeled_trajectories")

    # read label file and initialize label index:
    labels_t_start, labels_t_end, labels_labels = read_trajectory_labels(target_directory + "/labels.txt")
    label_index = 0

    # get sorted trajectory filenames
    sorted_trajectory_names = os.listdir(target_directory + "/Trajectory")
    sorted_trajectory_names = sorted(sorted_trajectory_names, key=lambda x: int(x.split(".")[0]))

    # iterate through gps path files:
    for file_name in sorted_trajectory_names:

        # get trajectory:
        times, latitudes, longitudes, altitudes = read_trajectory(target_directory + "/Trajectory/" + file_name)
        for t in times:

            # skip all labels of past times:
            while labels_t_end[label_index] < t:
                label_index += 1

            if t < labels_t_start[label_index]:
                continue

            # TODO: if not continued: you can now copy / store stuff ...
            else:
                print("yo: {}".format(t))
                print(file_name)
                print(label_index)
                print(labels_t_start[label_index])
                print(labels_t_end[label_index])

                exit()
            # print(labels_t_start[0])
            # print(labels_t_end[0])
            # print(labels_t_start[label_index])
            # print(labels_t_end[label_index])
            # print(t)
            # break

    # print(label_index)
    # print(len(labels_labels))
    # print(len(os.listdir(target_directory + "/Trajectory")))


def create_map_with_marker():
    # https: // developers.google.com / maps / documentation
    # https://developers.google.com/maps/documentation/javascript/adding-a-google-map
    pass


def main():
    # trajectory_path = "data/trajectories/010/Trajectory/20070804033032.plt"
    # _, _, _, _ = read_trajectory(trajectory_path)
    # label_path = "data/trajectories/010/labels.txt"
    # read_trajectory_labels(label_path)
    target_directory = "data/trajectories/010"
    label_trajectories(target_directory)

def main_data_import():
    tmp_data_path = "/home/julius/Downloads/Geolife Trajectories 1.3/Data/"
    workspace_data_path = "data/trajectories/"
    copy_useful_data_to_workspace(tmp_data_path, workspace_data_path)


if __name__ == '__main__':
    main()
    # main_data_import()
