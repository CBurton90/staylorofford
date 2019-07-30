"""
Before running this code:
- download .csv.xlsx files from google-drive
- using ssconvert, convert the file from xlsx to csv:
    for file in `ls *xlsx`; do ssconvert $file ${file:0:12}; rm $file; done
"""

import argparse
import datetime
import glob
import math
import matplotlib.pyplot as plt


def parse_sorted_path(sorted_path_file):

    """

    Parse rows of path file in as path points,
    and calculate distance of each point along the path

    :param sorted_path_file: path to sorted path file
    :return: list of path point coordinates, distances of each point
    """

    path_points = [[], [], []]
    distances = []

    with open(sorted_path_file, 'r') as openfile:

        header = '0'
        for row in openfile:

            # Ignore csv header

            try:
                header += 1
            except:
                header = int(header)
                continue

            cols = row.split(',')

            path_points[0].append(float(cols[0]))
            path_points[1].append(float(cols[1]))
            path_points[2].append(float(cols[2]))
            distances.append(float(cols[3]))

    return path_points, distances


def calc_distance(p1, p2):

    """

    Calculate the distance between two points in 2D space.

    :param p1: point 1 position [X, Y]
    :param p2: point 2 position [X, Y]
    :return: distance between p1 and p2
    """

    # Calculate distance

    d = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    return d


def cross_product(a, b):

    """
    Do cross product between a and b.
    """

    c = [a[1] * b[2] - a[2] * b[1],
         a[2] * b[0] - a[0] * b[2],
         a[0] * b[1] - a[1] * b[0]]

    return c


def dot_product(a, b):

    """
    Do dot product between a and b.
    """

    c = a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    return c


def normalise(a):

    """
    Return the normalised version of a and the magnitude of a.
    """

    a_mag = 0
    a_norm = []

    for value in a:
        a_mag += value ** 2
    a_mag = math.sqrt(a_mag)

    for value in a:
        a_norm.append(value / a_mag)

    return a_norm, a_mag


if __name__ == "__main__":

    # Parse arguments

    parser = argparse.ArgumentParser(description='What does this script do?')
    parser.add_argument('sorted_northgoing_path_csv', type=str, help="Path to csv file containing sorted"
                                                                     " northgoing path points")
    parser.add_argument('sorted_southgoing_path_csv', type=str, help="Path to csv file containing sorted"
                                                                     "southgoing path points")
    parser.add_argument('file_directory', type=str, help="Path to directory containing time series csv files")
    parser.add_argument('--northgoing_gates', type=str, help="Optional: distances along northgoing path to begin/end "
                                                             "analysis at. Format is:"
                                                             "northgoing start distance,northgoing end distance, in m, "
                                                             "e.g. 0,1000")
    parser.add_argument('--southgoing_gates', type=str, help="Optional: distances along southgoing path to begin/end "
                                                             "analysis at. Format is:"
                                                             "southgoing start distance,southgoing end distance, in m, "
                                                             "e.g. 0,1000")
    parser.add_argument('--accuracy', type=int, help="Optional: location accuracy value above which to discard data " +
                                                     "points. Default = 10 m")
    parser.add_argument('--threshold', type=int, help="Optional: distance of data point from path at which data point "
                                                      "is discarded. Default = 10 m")
    args = parser.parse_args()

    northgoing_path_file = args.sorted_northgoing_path_csv
    southgoing_path_file = args.sorted_southgoing_path_csv
    file_dir = args.file_directory
    northgoing_gates = args.northgoing_gates
    southgoing_gates = args.southgoing_gates
    accuracy = args.accuracy
    threshold = args.threshold

    # Parse commute point lists

    northgoing_point_list, northgoing_distance = parse_sorted_path(northgoing_path_file)
    southgoing_point_list, southgoing_distance = parse_sorted_path(southgoing_path_file)
    point_lists = [northgoing_point_list, southgoing_point_list]
    distance_lists = [northgoing_distance, southgoing_distance]

    # Prepare analysis lists

    distances = [[], []]
    times = [[], []]

    # Parse time series data in files

    data_columns = ['time', 'X', 'Y', 'accuracy']
    dc_idx = [3, 0, 1, 7]  # indices of data columns in data files
    northgoing_data_lists = [[] for i in range(len(data_columns))]
    southgoing_data_lists = [[] for i in range(len(data_columns))]
    data_lists = [northgoing_data_lists, southgoing_data_lists]

    if not accuracy:  # If no accuracy is given, set to default 10 m
        accuracy = 10
    if not threshold:  # If no threshold is given, set to default 10 m
        threshold = 10

    csv_files = glob.glob(file_dir + '*csv')
    for csv_file in csv_files:
        all_data_lists = [[] for i in range(len(data_columns))]
        with open(csv_file, 'r') as openfile:
            rc = 0
            for row in openfile:

                # Ignore csv header

                if rc == 0:
                    rc += 1
                    continue
                elif rc == 1:
                    reference_time = datetime.datetime.strptime(row.split(',')[3][:19], '%Y-%m-%dT%H:%M:%S')
                    rc += 1

                # Extract data into data_lists

                cols = row.split(',')

                # Determine if the point's accuracy is sufficient

                if float(cols[dc_idx[data_columns.index('accuracy')]].replace("\"", "")) > accuracy:
                    continue

                # Parse the data

                for n in range(len(data_columns)):
                    try:
                        all_data_lists[n].append((datetime.datetime.strptime(cols[dc_idx[n]][:19], '%Y-%m-%dT%H:%M:%S') -
                                                reference_time).total_seconds())
                    except:
                        all_data_lists[n].append(float(cols[dc_idx[n]].replace("\"", "")))

        # Split the data list into north- and south-going

        time_steps = []
        for i in range(1, len(all_data_lists[0])):
            time_steps.append(abs(all_data_lists[0][i - 1] - all_data_lists[0][i]))
        if max(time_steps) > 3600:  # If there is a time step of over an hour, i.e. a work day
            jump_time = all_data_lists[0][time_steps.index(max(time_steps))]
            for k in range(len(all_data_lists[0])):
                if all_data_lists[0][k] <= jump_time:  # north-going is before the work day
                    m = 0
                else:
                    m = 1
                for n in range(len(data_columns)):
                    data_lists[m][n].append(all_data_lists[n][k])
        else:
            if all_data_lists[2][-1] - all_data_lists[2][0] > 0:  # north-going
                m = 0
            else:  # otherwise south-going
                m = 1
            for n in range(len(data_columns)):
                data_lists[m][n].extend(all_data_lists[n])

    # Calculate distances of each data point along the path

    for m in range(len(data_lists)):
        for n in range(len(data_lists[m][0])):

            # First, find those vertices adjacent to the data point

            distance_sums = []
            data_point = [data_lists[m][1][n], data_lists[m][2][n]]
            for k in range(1, len(point_lists[m][0])):
                vertex_points = [[point_lists[m][0][k - 1], point_lists[m][1][k - 1]],
                                 [point_lists[m][0][k], point_lists[m][1][k]]]

                # Calculate the cumulative distance from the vertices to the data point

                distance_sum = 0
                for vertex_point in vertex_points:
                    distance_sum += calc_distance(data_point, vertex_point)

                # The distance sum will be smallest when the vertices surround the data point, so
                # save all the distance sums, then find the minima to get those vertices about the data point

                distance_sums.append(distance_sum)

            # Find the minimum distance sum, the adjacent vertices are those about that distance sum

            idx = distance_sums.index(min(distance_sums))
            vertex_points = [[point_lists[m][0][idx - 1], point_lists[m][1][idx - 1]],
                             [point_lists[m][0][idx], point_lists[m][1][idx]]]

            # Translate vertices and data point positions into vectors relative to the "behind" vertex

            direction_vector = [vertex_points[1][0] - vertex_points[0][0],
                                vertex_points[1][1] - vertex_points[0][1],
                                0]
            relative_data_point = [data_point[0] - vertex_points[0][0],
                                   data_point[1] - vertex_points[0][1],
                                   0]

            # Using vectors, calculate distance of the point along the path and from the path

            try:
                distance_on_line = dot_product(direction_vector, relative_data_point) / normalise(direction_vector)[1]

                data_vertex_cross_product = cross_product(direction_vector, relative_data_point)
                distance_from_line = ((data_vertex_cross_product[2] / abs(data_vertex_cross_product[2])) *
                                      normalise(data_vertex_cross_product)[1] / normalise(direction_vector)[1])

            except:  # Fails if direction vector has length 0
                pass

            # If the point is not too far from the line

            if distance_from_line <= threshold:
                times[m].append(data_lists[m][0][n])
                distances[m].append(distance_lists[m][idx] + distance_on_line)

    # Apply gates

    if northgoing_gates or southgoing_gates:
        gates = [[], []]
        if not northgoing_gates:
            gates[0] = ['0', '999999']
        else:
            gates[0] = northgoing_gates.split(',')

        if not southgoing_gates:
            gates[1] - ['0', '999999']
        else:
            gates[1] = southgoing_gates.split(',')

        gated_times = [[], []]
        gated_distances = [[], []]
        for m in range(len(times)):

            gate_time = 0
            gate_start_distance = float(gates[m][0])
            gate_end_distance = float(gates[m][1])
            for n in range(len(times[m])):
                gated_distance = distances[m][n] - gate_start_distance
                if gated_distance < 0:  # Record the past time up until the gate distance is passed
                    gate_time = times[m][n]
                elif distances[m][n] <= gate_end_distance:
                    # Once the gate distance is passed, save times relative to the last time pre-gate, unless
                    # the end gate has been passed also
                    gated_times[m].append(times[m][n] - gate_time)
                    gated_distances[m].append(gated_distance)

        times = gated_times
        distances = gated_distances

    # Need to do something else with the data to get it in a format that can handle partial datasets

    for m in range(len(times)):

        plt.scatter(distances[m], times[m])
        plt.show()
