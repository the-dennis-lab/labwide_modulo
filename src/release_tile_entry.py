#!/usr/bin/env python 3
#  -*- coding: utf8 -*-

"""
inputs:

optional_inputs:

outputs:

optional_outputs:

created: 20250219
author:ns

"""

if __name__ == "__main__":
    #imports
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import math
    import cv2
    import os
    import sys

    #functions

    def dist_from_releasetile_zaber(df, session_locs):


        """
        calculates distance of zaber x,y with all release_tiles and makes a new df. Its written in a way to be intuitive to the reader.

        Args:
            df: in this case it is the all_params csv
            session_locs: any df which has the ccf adjusted ls and ax3 values

        Returns:
            df: all_params with distance calculated between zaber x,y and release tile centers for all release tile in separate column
        """


        releasetile_1x = session_locs.ls_ccf_adjusted[0]
        releasetile_1y = session_locs.ax3_ccf_adjusted[0]
        releasetile_2x = session_locs.ls_ccf_adjusted[1]
        releasetile_2y = session_locs.ax3_ccf_adjusted[1]
        releasetile_3x = session_locs.ls_ccf_adjusted[2]
        releasetile_3y = session_locs.ax3_ccf_adjusted[2]
        releasetile_4x = session_locs.ls_ccf_adjusted[3]
        releasetile_4y = session_locs.ax3_ccf_adjusted[3]
        releasetile_5x = session_locs.ls_ccf_adjusted[4]
        releasetile_5y = session_locs.ax3_ccf_adjusted[4]
        releasetile_6x = session_locs.ls_ccf_adjusted[5]
        releasetile_6y = session_locs.ax3_ccf_adjusted[5]
        releasetile_7x = session_locs.ls_ccf_adjusted[6]
        releasetile_7y = session_locs.ax3_ccf_adjusted[6]
        releasetile_8x = session_locs.ls_ccf_adjusted[7]
        releasetile_8y = session_locs.ax3_ccf_adjusted[7]
        releasetile_9x = session_locs.ls_ccf_adjusted[8]
        releasetile_9y = session_locs.ax3_ccf_adjusted[8]
        releasetile_10x = session_locs.ls_ccf_adjusted[9]
        releasetile_10y = session_locs.ax3_ccf_adjusted[9]
        releasetile_11x = session_locs.ls_ccf_adjusted[10]
        releasetile_11y = session_locs.ax3_ccf_adjusted[10]
        releasetile_12x = session_locs.ls_ccf_adjusted[11]
        releasetile_12y = session_locs.ax3_ccf_adjusted[11]
        releasetile_13x = session_locs.ls_ccf_adjusted[12]
        releasetile_13y = session_locs.ax3_ccf_adjusted[12]
        releasetile_14x = session_locs.ls_ccf_adjusted[13]
        releasetile_14y = session_locs.ax3_ccf_adjusted[13]
        releasetile_15x = session_locs.ls_ccf_adjusted[14]
        releasetile_15y = session_locs.ax3_ccf_adjusted[14]
        releasetile_16x = session_locs.ls_ccf_adjusted[15]
        releasetile_16y = session_locs.ax3_ccf_adjusted[15]


        dist_from_1 = []
        dist_from_2 = []
        dist_from_3 = []
        dist_from_4 = []
        dist_from_5 = []
        dist_from_6 = []
        dist_from_7 = []
        dist_from_8 = []
        dist_from_9 = []
        dist_from_10 = []
        dist_from_11 = []
        dist_from_12 = []
        dist_from_13 = []
        dist_from_14 = []
        dist_from_15 = []
        dist_from_16 = []


        for i in np.arange(0, len(df)):
            dist_from_1.append(math.dist([releasetile_1x, releasetile_1y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_2.append(math.dist([releasetile_2x, releasetile_2y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_3.append(math.dist([releasetile_3x, releasetile_3y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_4.append(math.dist([releasetile_4x, releasetile_4y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_5.append(math.dist([releasetile_5x, releasetile_5y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_6.append(math.dist([releasetile_6x, releasetile_6y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_7.append(math.dist([releasetile_7x, releasetile_7y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_8.append(math.dist([releasetile_8x, releasetile_8y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_9.append(math.dist([releasetile_9x, releasetile_9y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_10.append(math.dist([releasetile_10x, releasetile_10y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_11.append(math.dist([releasetile_11x, releasetile_11y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_12.append(math.dist([releasetile_12x, releasetile_12y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_13.append(math.dist([releasetile_13x, releasetile_13y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_14.append(math.dist([releasetile_14x, releasetile_14y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_15.append(math.dist([releasetile_15x, releasetile_15y],[df.zaber_x[i], df.zaber_y[i]]))
            dist_from_16.append(math.dist([releasetile_16x, releasetile_16y],[df.zaber_x[i], df.zaber_y[i]]))

        df = df[['zaber_x', 'zaber_y','timestamp', 'relative_time', 'frame_no', 'triggered', 'trigger', 'dist_travelled', 'speed', 'chirped', 'chirp_bouts', 'chirp_loc', 'dlc_node']]

        df["dist_from_1"] = dist_from_1
        df["dist_from_2"] = dist_from_2
        df["dist_from_3"] = dist_from_3
        df["dist_from_4"] = dist_from_4
        df["dist_from_5"] = dist_from_5
        df["dist_from_6"] = dist_from_6
        df["dist_from_7"] = dist_from_7
        df["dist_from_8"] = dist_from_8
        df["dist_from_9"] = dist_from_9
        df["dist_from_10"] = dist_from_10
        df["dist_from_11"] = dist_from_11
        df["dist_from_12"] = dist_from_12
        df["dist_from_13"] = dist_from_13
        df["dist_from_14"] = dist_from_14
        df["dist_from_15"] = dist_from_15
        df["dist_from_16"] = dist_from_16

        return df


    #sysarvs
    # Check if the folder path is provided as a command-line argument

    os.chdir(os.path.dirname(__file__))

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        print(f"Folder path provided: {folder_path}")
    else:
        print("No folder path provided. Please provide a folder path as a command-line argument.")

    if not os.path.isdir(folder_path):
        print(f"Error: The folder path '{folder_path}' is not valid.")
        sys.exit(1)

    # Check if the output folder path is provided as a command-line argument
    if len(sys.argv) > 2:
        output_folder_path = sys.argv[2]
        print(f"Output folder path provided: {output_folder_path}")
    else:
        output_folder_path = folder_path
        print("No output folder path provided. Using input folder path as output folder path.")

    if not os.path.isdir(output_folder_path):
        print(f"Error: The folder path '{output_folder_path}' is not valid.")
        sys.exit(1)




    session_adjusted_location_files = []
    all_params_files = []
    for file in os.listdir(folder_path):
        if "session_adjusted_location" in file:
            session_adjusted_location_files.append(file)
        if "all_params_file" in file:
            all_params_files.append(file)

    print("number of session_adjusted_location files found = {}".format(len(session_adjusted_location_files)))
    print("number of all_params files found = {}".format(len(all_params_files)))




    #outputs
