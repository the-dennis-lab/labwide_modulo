import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

import os
import sys

def make_ccf_adjusted_all_params(df, all_params, ccf):

    """
    use ccf csv to make new columns in the all_params, with corrected locations, locations tile name, ccf_zaber_x, ccf_zaber_y

    Args:
    1. df = locations input file (this is saved out in each folder of session data)
    2. all_params = this is the csv generated from the script (generate_all_params)
    3. ccf = this is the standard reference file for the centres for 157 tiles, this is saved in the data folder of the github repo.
    """

    #read the locations column fron all_params and make a list of ls and ax3 for all 16 locations
    location_val_list = all_params.locations[0]
    location_val_list = [int(x) for x in location_val_list.strip('[]').split(',')]
    #assign odd values as ls
    ls=location_val_list[::2]
    #assign even values as ax3
    ax3=location_val_list[1::2]


    #drop the time_stamp from df
    df[16] = file_timestring
    df = df.rename(columns = {16:'time_stamp'})
    df = df.drop('time_stamp', axis=1)


    #get tile_names from location_input file
    tile_name=[]
    tile_name = df.iloc[0].tolist()
    print(tile_name)

    #make a new df for session_locs and add tile_name, ls, and ax3
    session_locs=pd.DataFrame()
    session_locs['tile_name']=tile_name
    session_locs['tile_x']=ls[0:16]
    session_locs['tile_y']=ax3[0:16]


    # compare the values in session locs and ccf and get an median offset values
    ccf_lss=[]
    ccf_ax3s=[]
    for val in session_locs.tile_name:
        idx = np.where(ccf.name==val)[0][0]
        ccf_lss.append(ccf.ls[idx])
        ccf_ax3s.append(ccf.ax3[idx])
    session_locs['ls_offset']=session_locs.tile_x-ccf_lss
    session_locs['ax3_offset']=session_locs.tile_y-ccf_ax3s
    session_locs['ccf_lss'] = ccf_lss
    session_locs['ccf_ax3s'] = ccf_ax3s
    #create a list of location ls and ax3 in a single list as per the ccf csv
    ccf_locations = [val for pair in zip(ccf_lss, ccf_ax3s) for val in pair]
    #get median with first six values of the offset, we use first six because these are the only once manually corrected before every experimental session
    med_lsoff= np.median(session_locs.ls_offset[0:6])
    med_axoff = np.median(session_locs.ax3_offset[0:6])

    # to correct all locations in the all_params locations column from ccf and get a new list of locations_ccf_corrected
    # now adjust the entire ccf df using the median offset values from session_locs
    session_adjusted_ccf = ccf
    session_adjusted_ccf["ls_adjusted"] = session_adjusted_ccf.ls + med_lsoff
    session_adjusted_ccf["ax3_adjusted"] = session_adjusted_ccf.ax3 + med_axoff
    #session_adjusted_ccf

    #from session adjusted ccf df get the ccf adjusted values for ls and ax3 for the tile_id in session_locs
    session_adjusted_ls=[]
    session_adjusted_ax3=[]
    for val in session_locs.tile_name:
        idx = np.where(session_adjusted_ccf.name==val)[0][0]
        session_adjusted_ls.append(session_adjusted_ccf.ls_adjusted[idx])
        session_adjusted_ax3.append(session_adjusted_ccf.ax3_adjusted[idx])
    locations_ccf_corrected = [val for pair in zip(session_adjusted_ls, session_adjusted_ax3) for val in pair]


    #add all the lists to the all_params df and save it as a new ccf adjusted all_params df

    #locations which are now ccf corrected according to the session
    all_params['locations_ccf_corrected'] = None
    all_params.at[0,'locations_ccf_corrected']=locations_ccf_corrected

    #locations release tile location names
    all_params["rel_tile_location_name"] = None
    all_params.at[0,"rel_tile_location_name"] = tile_name

    #locations as per the ccf csv file
    all_params["ccf_locations"] = None
    all_params.at[0,"ccf_locations"] = ccf_locations

    #ccf corrected zaber_x and zaber_y
    all_params["ccf_zaber_x"] = (all_params["zaber_x"] - med_lsoff)
    all_params["ccf_zaber_y"] = (all_params["zaber_y"] - med_axoff)

    ccf_adj_all_params = all_params

    return ccf_adj_all_params
