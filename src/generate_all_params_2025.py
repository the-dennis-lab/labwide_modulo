"""
Animal Tracking Data Processing Script

Required inputs:
1. Folder location containing tracking data files

Optional inputs:
1. Output folder location (default: ../data/results)

Outputs:
1. A summary CSV file with processed data

This script is designed to:
- Parse and synchronize multiple experiment data files (tracking, rig info, chirps, etc.)
- Extract and compute relevant features (e.g., speed, locations, event times)
- Output a summary CSV for each experiment/animal
"""

__author__ = 'ns'
__credits__ = ['ns', 'ejd']
__maintainer__ = 'ns'
__email__ = 'shettigarn@hhmi.org'
__license__ = 'MIT'
__status__ = 'development'

# Standard imports
import os
import sys
import math
from typing import List, Dict, Tuple, Optional, Union
import logging
from datetime import datetime
import pandas.errors

# Third-party imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Helper Functions for Timestamp Processing

def bonsai_timestamp_split(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split Bonsai timestamps into hour, minute, and second columns for easier time calculations.
    Assumes 'timestamp' column is present in the DataFrame.
    """
    df = df.copy()  # Avoid SettingWithCopyWarning if df is a slice
    split_cols = df['timestamp'].str.split('T|:|-', expand=True)
    df.loc[:, 'hours'] = split_cols[3]
    df.loc[:, 'minutes'] = split_cols[4]
    df.loc[:, 'seconds'] = split_cols[5]
    return df


def absolute_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate absolute time in seconds from the split hour, minute, and second columns.
    Adds an 'absolute_time' column to the DataFrame.
    """
    df = df.copy()  # optional: ensure df is a fresh copy to avoid chained assignment issues
    df.loc[:, 'absolute_time'] = (
        df['hours'].astype(float) * 3600 +
        df['minutes'].astype(float) * 60 +
        df['seconds'].astype(float)
    )
    return df


def relative_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate time relative to the first timestamp in the DataFrame.
    Adds a 'relative_time' column.
    """
    df["relative_time"] = df.absolute_time - df.absolute_time.iloc[0]
    return df


def calculate_distance(point1: list, point2: list) -> float:
    """
    Compute Euclidean distance between two points (2D coordinates).
    """
    return math.dist(point1, point2)


def calculate_speed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute speed for each row based on zaber_x/y positions and relative_time.
    Adds 'time_travelled', 'dist_travelled', and 'speed' columns.
    """
    # Calculate time between consecutive points
    df["time_travelled"] = df.relative_time.diff().shift(-1)
    df["time_travelled"] = df["time_travelled"].fillna(0)

    # Calculate distance traveled between consecutive points
    dist_travelled = [0]  # First point has no distance traveled
    for i in range(1, len(df)):
        dist = calculate_distance(
            [df.zaber_x.iloc[i-1], df.zaber_y.iloc[i-1]],
            [df.zaber_x.iloc[i], df.zaber_y.iloc[i]]
        )
        dist_travelled.append(dist)

    df["dist_travelled"] = dist_travelled

    # Calculate speed (avoid division by zero)
    df["speed"] = np.where(
        df.time_travelled > 0,
        df.dist_travelled / df.time_travelled,
        0
    )

    return df




def add_locations(df: pd.DataFrame, locations_file: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'locations' column to the DataFrame, containing all tile positions for reference.

    Args:
        df: DataFrame with tracking data
        locations_file: DataFrame with tile locations

    Returns:
        DataFrame with added 'locations' column
    """
    # Set column names for 16 tile version
    columns = []
    for i in range(1, 17):
        columns.extend([f'releasetile_{i}x', f'releasetile_{i}y'])

    locations_file.columns = columns

    # Extract location values
    locations = []
    for col in columns:
        locations.append(locations_file[col].iloc[0])

    # Create a locations column to store all the tile positions
    df["locations"] = np.nan
    df["locations"] = df["locations"].astype('object')  # Change to object type to store list
    df.at[0, 'locations'] = locations

    return df


# File Processing Functions

def find_matching_file(file_list: list, file_timestring: str, search_depth: int = 3) -> tuple:
    """
    Find the best-matching file in file_list based on a timestamp string, with fallback to partial matches.
    Returns a tuple (matching_files, good_idx).

    Args:
        file_list: List of available files
        file_timestring: Target timestamp string to match
        search_depth: Number of attempts with shortened timestring to try

    Returns:
        Tuple of (matching_files, good_idx)
    """
    # Try exact match first
    matching_files = [file for file in file_list if file_timestring in file]

    # Try shortened timestring if no exact match
    for i in range(1, search_depth + 1):
        if not matching_files:
            shortened_timestring = file_timestring[:min(len(file_timestring), 5-i)]
            matching_files = [file for file in file_list if shortened_timestring in file]
            if matching_files:
                logger.info(f"Match found using shortened timestring: {shortened_timestring}")
                break

    # If files found, return the first match
    if matching_files:
        logger.info(f"current matched file and processing: {matching_files}")
        return matching_files, 0

    # No match found
    logger.warning(f"No matching file found for timestring: {file_timestring}")
    return [], -1


def clean_locations_file(locations_file: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the locations file, ensuring correct column names and integer values.

    Args:
        locations_file: DataFrame with raw locations data

    Returns:
        Cleaned DataFrame ready for processing
    """
    # Make a copy to avoid modifying the original DataFrame or triggering warnings
    df = locations_file.copy()

    # Limit to first 32 columns if necessary
    if len(df.columns) > 32:
        df = df.iloc[:, :32]

    # Convert column names to string
    df.columns = df.columns.astype(str)

    # Clean and convert values in each column
    for col in df.columns:
        # Remove non-digit characters and convert to int safely
        df.loc[:, col] = (
            df[col]
            .astype(str)
            .str.replace(r'\D', '', regex=True)
            .replace('', '0')  # handle empty strings after replacement
            .astype(int)
        )

    return df


def process_zaber_dlc_file(zaber_dlc_file: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the Zaber DLC tracking file: set columns, parse timestamps, and drop unnecessary columns.

    Args:
        zaber_dlc_file: DataFrame with raw Zaber DLC data

    Returns:
        Processed DataFrame with relevant tracking information
    """
    # Set column names based on the number of columns
    if len(zaber_dlc_file.columns) == 6:
        zaber_dlc_file.columns = ['dlc_x', 'dlc_y', 'chirp', 'zaber_x', 'zaber_y', 'timestamp']
    elif len(zaber_dlc_file.columns) == 7:
        zaber_dlc_file.columns = ['dlc_x', 'dlc_y', 'chirp', 'zaber_x', 'zaber_y', 'model_confidence', 'timestamp']

    # Remove chirp column
    zaber_dlc_file = zaber_dlc_file.drop('chirp', axis=1)

    # Process timestamps
    zaber_dlc_file = bonsai_timestamp_split(zaber_dlc_file)
    zaber_dlc_file = absolute_time(zaber_dlc_file)
    zaber_dlc_file = relative_time(zaber_dlc_file)

    # Remove unnecessary columns
    zaber_dlc_file = zaber_dlc_file.drop(['hours', 'minutes', 'seconds'], axis=1)

    return zaber_dlc_file


def process_cam_frame_file(cam_frame_file: pd.DataFrame, zaber_dlc_file: pd.DataFrame) -> pd.DataFrame:
    """
    Synchronize camera frame numbers with tracking data based on closest timestamps.
    Adds 'frame_no' to the tracking DataFrame.

    Args:
        cam_frame_file: DataFrame with raw camera frame data
        zaber_dlc_file: DataFrame with Zaber DLC tracking data

    Returns:
        Updated zaber_dlc_file with synchronized frame numbers
    """
    try:
        # Extract and process frame data
        cam_frame_file = cam_frame_file[[16]]
        cam_frame_file.reset_index(inplace=True)
        cam_frame_file.columns = ['frame_no', 'timestamp']
        cam_frame_file.loc[:, 'frame_no'] = cam_frame_file['frame_no'] + 1

        # Process timestamps
        cam_frame_file = bonsai_timestamp_split(cam_frame_file)
        cam_frame_file = absolute_time(cam_frame_file)
        cam_frame_file["relative_time"] = cam_frame_file.absolute_time - zaber_dlc_file.absolute_time.iloc[0]
        cam_frame_file = cam_frame_file.drop(columns=['timestamp', 'hours', 'minutes', 'seconds', 'absolute_time'])

        # Add frame numbers to zaber data
        zaber_dlc_file['frame_no'] = np.nan

        # Match frames to zaber data based on closest time
        for i in range(len(cam_frame_file)):
            index = np.argmin(np.abs(zaber_dlc_file['relative_time'] - cam_frame_file.relative_time.iloc[i]))
            zaber_dlc_file.loc[index, 'frame_no'] = cam_frame_file.frame_no.iloc[i]

        # Remove rows with missing frame numbers (optional)
        zaber_dlc_file = zaber_dlc_file.dropna(subset=["frame_no"]).reset_index(drop=True)

        # Calculate speed
        zaber_dlc_file = calculate_speed(zaber_dlc_file)

        return zaber_dlc_file

    except Exception as e:
        logger.error(f"Error processing camera frame file: {e}")
        return zaber_dlc_file


def process_chirp_file(chirp_file: pd.DataFrame, zaber_dlc_file: pd.DataFrame) -> pd.DataFrame:
    """
    Merge chirp event data with tracking data, assigning chirp bouts and locations to frames.

    Args:
        chirp_file: DataFrame with raw chirp data
        zaber_dlc_file: DataFrame with Zaber DLC tracking data

    Returns:
        Updated zaber_dlc_file with chirp event information
    """
    try:
        # Set column names
        if len(chirp_file.columns) == 2:
            chirp_file.columns = ["timestamp", "crickets_eaten"]
        elif len(chirp_file.columns) >= 3:
            cols = ["timestamp", "crickets_eaten"] + [f"drop{i}" for i in range(1, len(chirp_file.columns)-1)]
            chirp_file.columns = cols[:len(chirp_file.columns)]
            # Drop extra columns if they exist
            drop_cols = [col for col in chirp_file.columns if col.startswith("drop")]
            chirp_file = chirp_file.drop(columns=drop_cols)

        # Map cricket values to locations
        chirp_loc = np.zeros(len(chirp_file))
        mapping = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: float("nan")}

        for i in range(len(chirp_file)):
            val = chirp_file.crickets_eaten.iloc[i]
            chirp_loc[i] = mapping.get(val, float("nan"))

        chirp_file['chirp_loc'] = chirp_loc

        # Process timestamps
        chirp_file = bonsai_timestamp_split(chirp_file)
        chirp_file = absolute_time(chirp_file)
        chirp_file["relative_time"] = chirp_file.absolute_time - zaber_dlc_file.absolute_time.iloc[0]

        # Keep only relevant columns
        chirp_file = chirp_file[["crickets_eaten", "chirp_loc", "relative_time"]]

        # Merge chirp data with zaber data based on closest time
        chirp_file = pd.merge_asof(chirp_file, zaber_dlc_file, on='relative_time', direction='nearest')

        # Calculate chirp bouts
        chirp_file['chirp_bouts'] = np.zeros(len(chirp_file))
        bout_num = 0

        for idx in range(len(chirp_file)):
            if idx == 0:
                bout_num += 1
            else:
                # Check if position changed between chirps
                dist_val = calculate_distance(
                    [chirp_file.zaber_x.iloc[idx-1], chirp_file.zaber_y.iloc[idx-1]],
                    [chirp_file.zaber_x.iloc[idx], chirp_file.zaber_y.iloc[idx]]
                )
                if dist_val != 0:
                    bout_num += 1

            chirp_file.loc[idx, 'chirp_bouts'] = bout_num

        # Add chirp data to zaber file
        zaber_dlc_file['chirped'] = np.nan
        zaber_dlc_file['chirp_bouts'] = np.nan
        zaber_dlc_file['chirp_loc'] = np.nan

        for i in range(len(chirp_file)):
            index = np.argmin(np.abs(zaber_dlc_file['relative_time'] - chirp_file.relative_time.iloc[i]))
            zaber_dlc_file.loc[index, 'chirped'] = 1
            zaber_dlc_file.loc[index, 'chirp_bouts'] = chirp_file.chirp_bouts.iloc[i]
            zaber_dlc_file.loc[index, 'chirp_loc'] = chirp_file.chirp_loc.iloc[i]

        return zaber_dlc_file

    except Exception as e:
        logger.error(f"Error processing chirp file: {e}")
        # Initialize columns even if processing failed
        zaber_dlc_file['chirped'] = np.nan
        zaber_dlc_file['chirp_bouts'] = np.nan
        zaber_dlc_file['chirp_loc'] = np.nan
        return zaber_dlc_file


def process_release_trigger_file(release_trigger_file: pd.DataFrame, zaber_dlc_file: pd.DataFrame) -> pd.DataFrame:
    """
    Merge release trigger events with tracking data, marking frames as triggered.

    Args:
        release_trigger_file: DataFrame with raw release trigger data
        zaber_dlc_file: DataFrame with Zaber DLC tracking data

    Returns:
        Updated zaber_dlc_file with release trigger information
    """
    try:
        # Initialize trigger columns
        zaber_dlc_file['triggered'] = np.nan
        zaber_dlc_file['trigger'] = np.nan

        # Set column names
        release_trigger_file.columns = ['trigger', 'timestamp']

        # Process timestamps
        release_trigger_file = bonsai_timestamp_split(release_trigger_file)
        release_trigger_file = absolute_time(release_trigger_file)
        release_trigger_file["relative_time"] = release_trigger_file.absolute_time - zaber_dlc_file.absolute_time.iloc[0]

        # Add trigger data to zaber file
        for i in range(len(release_trigger_file)):
            index = np.argmin(np.abs(zaber_dlc_file['relative_time'] - release_trigger_file.relative_time.iloc[i]))
            zaber_dlc_file.loc[index, 'triggered'] = 1
            zaber_dlc_file.loc[index, 'trigger'] = release_trigger_file.trigger.iloc[i]

        return zaber_dlc_file

    except Exception as e:
        logger.error(f"Error processing release trigger file: {e}")
        return zaber_dlc_file


def process_dlc_nodes_file(dlc_nodes_file: pd.DataFrame, zaber_dlc_file: pd.DataFrame) -> pd.DataFrame:
    """
    Merge DLC node tracking data with main tracking data, flagging frames with valid node detections.

    Args:
        dlc_nodes_file: DataFrame with raw DLC nodes data
        zaber_dlc_file: DataFrame with Zaber DLC tracking data

    Returns:
        Updated zaber_dlc_file with DLC node tracking information
    """
    try:
        if dlc_nodes_file is None or dlc_nodes_file.empty:
            zaber_dlc_file['dlc_node'] = np.nan
            print("No dlc_node file found to process.")
            return zaber_dlc_file

        # Initialize dlc_node column
        zaber_dlc_file['dlc_node'] = np.nan

        # Set column names
        columns = [f'point{i}' for i in range(1, 15)] + ['timestamp']
        dlc_nodes_file.columns = columns[:len(dlc_nodes_file.columns)]

        # Check for valid tracking data
        dlc_nodes = []
        for _, row in dlc_nodes_file.iterrows():
            # Check if all point columns are NaN
            if row[columns[:-1]].isna().all():
                dlc_nodes.append(0)  # No valid tracking
            else:
                dlc_nodes.append(1)  # Valid tracking

        dlc_nodes_file['dlc_node'] = dlc_nodes

        # Filter to keep only valid tracking data
        dlc_nodes_file = dlc_nodes_file[dlc_nodes_file['dlc_node'] == 1].reset_index(drop=True)

        # Process timestamps
        dlc_nodes_file = bonsai_timestamp_split(dlc_nodes_file)
        dlc_nodes_file = absolute_time(dlc_nodes_file)
        dlc_nodes_file["relative_time"] = dlc_nodes_file.absolute_time - zaber_dlc_file.absolute_time.iloc[0]

        # Add dlc_node data to zaber file
        for i in range(len(dlc_nodes_file)):
            index = np.argmin(np.abs(zaber_dlc_file['relative_time'] - dlc_nodes_file.relative_time.iloc[i]))
            zaber_dlc_file.loc[index, 'dlc_node'] = 1

        return zaber_dlc_file

    except Exception as e:
        logger.error(f"Error processing DLC nodes file: {e}")
        return zaber_dlc_file

def make_ccf_adjusted_all_params(zaber_dlc_file: pd.DataFrame, location_input_file: pd.DataFrame, ccf_file: str) -> pd.DataFrame:
    """
    Create a CCF-adjusted all_params DataFrame from zaber_dlc_file and a location input file.

    Args:
        zaber_dlc_file: DataFrame from an all_params file.
        location_input_file: Path to the location_inputs CSV.
        ccf_file: Path to the standard reference CCF CSV.
        file_timestring: Unique identifier for the session.
        output_folder_path: Path where to save the resulting CSV.

    Returns:
        CCF-adjusted all_params DataFrame.
    """

    # Read input files
    df = location_input_file.copy()
    ccf = pd.read_csv(ccf_file)

    # Parse locations from all_params

    location_val_list = zaber_dlc_file['locations'].iloc[0]
    location_val_list = [int(x) for x in location_val_list]
    ls = location_val_list[::2]
    ax3 = location_val_list[1::2]

    # Drop and rename timestamp column in location_input
    df = df.rename(columns={16: 'time_stamp'})
    df = df.drop('time_stamp', axis=1)

    # Extract tile names from location input file
    tile_name = df.iloc[0].tolist()

    # Build session_locs DataFrame
    session_locs = pd.DataFrame({
        'tile_name': tile_name,
        'tile_x': ls[:16],
        'tile_y': ax3[:16]
    })

    # Match session tile names to CCF
    ccf_lss, ccf_ax3s = [], []

    for val in session_locs.tile_name:
        idx = np.where(ccf['name'] == val)[0][0]
        ccf_lss.append(ccf['ls'][idx])
        ccf_ax3s.append(ccf['ax3'][idx])

    session_locs['ls_offset'] = session_locs['tile_x'] - ccf_lss
    session_locs['ax3_offset'] = session_locs['tile_y'] - ccf_ax3s
    session_locs['ccf_lss'] = ccf_lss
    session_locs['ccf_ax3s'] = ccf_ax3s

    # Median offset from first 6 tiles
    med_lsoff = np.median(session_locs['ls_offset'][:6])
    med_axoff = np.median(session_locs['ax3_offset'][:6])

    # Adjust CCF reference with offsets
    session_adjusted_ccf = ccf.copy()
    session_adjusted_ccf['ls_adjusted'] = session_adjusted_ccf['ls'] + med_lsoff
    session_adjusted_ccf['ax3_adjusted'] = session_adjusted_ccf['ax3'] + med_axoff

    # Get adjusted locations from CCF
    session_adjusted_ls, session_adjusted_ax3 = [], []
    for val in session_locs.tile_name:
        idx = np.where(session_adjusted_ccf['name'] == val)[0][0]
        session_adjusted_ls.append(session_adjusted_ccf['ls_adjusted'][idx])
        session_adjusted_ax3.append(session_adjusted_ccf['ax3_adjusted'][idx])

    locations_ccf_corrected = [val for pair in zip(session_adjusted_ls, session_adjusted_ax3) for val in pair]
    ccf_locations = [val for pair in zip(ccf_lss, ccf_ax3s) for val in pair]

    # Update zaber_dlc_file (all_params)
    zaber_dlc_file = zaber_dlc_file.copy()
    zaber_dlc_file['locations_ccf_corrected'] = None
    zaber_dlc_file.at[0, 'locations_ccf_corrected'] = locations_ccf_corrected

    zaber_dlc_file['rel_tile_location_name'] = None
    zaber_dlc_file.at[0, 'rel_tile_location_name'] = tile_name

    zaber_dlc_file['ccf_locations'] = None
    zaber_dlc_file.at[0, 'ccf_locations'] = ccf_locations

    zaber_dlc_file['ccf_zaber_x'] = zaber_dlc_file['zaber_x'] - med_lsoff
    zaber_dlc_file['ccf_zaber_y'] = zaber_dlc_file['zaber_y'] - med_axoff



    return zaber_dlc_file


# Main processing function
def process_data(folder_path: str, output_folder: str = None) -> None:
    """
    Main function to process all experiment files in the given folder.
    For each experiment, synchronizes and merges all relevant data sources, then outputs a summary CSV.

    Args:
        folder_path: Path to the folder containing all data files
        output_folder: Optional path to the folder where results will be saved
    """
    # Validate folder exists
    if not os.path.isdir(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return

    # Set default output folder if not provided
    if output_folder is None:
        output_folder = folder_path
        os.makedirs(output_folder, exist_ok=True)

        # Find all relevant files in the folder
    file_categories = {
        'rig_info': [],
        'modulo_info': [],
        'zaber_dlc': [],
        'chirps': [],
        'dlc_nodes': [],
        'release_trigger': [],
        'locations': [],
        'location_inputs': [],  # ← NEW category
        'cam_frame': []
    }

    for file in os.listdir(folder_path):
        if "with_zaber" in file:
            file_categories['zaber_dlc'].append(file)
        elif "chirps" in file:
            file_categories['chirps'].append(file)
        elif "DLC_all" in file:
            file_categories['dlc_nodes'].append(file)
        elif "release_trigger" in file:
            file_categories['release_trigger'].append(file)
        elif "location_vals" in file:
            file_categories['locations'].append(file)
        elif file.startswith("location_inputs_"):
            file_categories['location_inputs'].append(file)  # ← NEW match
        elif "rig_info" in file:
            file_categories['rig_info'].append(file)
        elif "cam_frame" in file:
            file_categories['cam_frame'].append(file)
        elif "modulo_info" in file:
            file_categories['modulo_info'].append(file)

    # Process each set of related files (by timestamp)
    info_files = file_categories['rig_info'] if file_categories['rig_info'] else file_categories['modulo_info']

    for info_file in info_files:
        try:
            # Extract timestamp and animal name from info file
            info_path = os.path.join(folder_path, info_file)
            is_rig_info = "rig_info" in info_file

            # Read info file
            info_df = pd.read_csv(info_path, header=None)

            # Extract animal name
            if is_rig_info:
                # Handle rig_info file
                if len(info_df.columns) == 13:
                    info_df.columns = ['1', 'model_confidence', 'dlc_model_loc', 'model_snapshot_loc',
                                      'lockstep_img_loc', 'ax3_img_loc', '2', '3', '4', '5', '6',
                                      'animal_name', 'timestamp']
                elif len(info_df.columns) == 14:
                    info_df.columns = ['1', 'model_confidence', 'dlc_model_loc', 'model_snapshot_loc',
                                      'lockstep_img_loc', 'ax3_img_loc', '2', '3', '4', '5', '6',
                                      'animal_name', 'experiment_type', 'timestamp']

                filename_prefix = 9  # Length of "rig_info_" prefix
            else:
                # Handle modulo_info file
                info_df.drop(columns=info_df.columns[5:39], inplace=True, errors='ignore')
                info_df.columns = ['model_confidence', '1', '2', '3', '4', 'zaber_radius',
                                  'loudness_value', '41', '42', 'animal_name', 'experiment_type',
                                  'timestamp']
                filename_prefix = 12  # Length of "modulo_info_" prefix

            animal_name = info_df.animal_name.iloc[0].lower()
            logger.info(f"Processing data for animal: {animal_name}")
            logger.info(f"Processing data from info file: {info_file}")

            # Extract timestamp from filename
            file_base = os.path.basename(info_file)
            file_datetime = file_base[filename_prefix:-4]
            file_timestring = file_base.split('T')[1][:-4]

            # Process locations file
            location_filename, good_idx = find_matching_file(
                file_categories['locations'], file_timestring)

            if good_idx != -1 and location_filename:
                locations_file = pd.read_csv(
                    os.path.join(folder_path, location_filename[0]), header=None)
                locations_file = clean_locations_file(locations_file)

                # Process zaber_dlc file
                zaber_dlc_filename, good_idx = find_matching_file(
                    file_categories['zaber_dlc'], file_timestring)

                if good_idx != -1 and zaber_dlc_filename:
                    zaber_dlc_file = pd.read_csv(
                        os.path.join(folder_path, zaber_dlc_filename[0]), header=None)
                    zaber_dlc_file = process_zaber_dlc_file(
                        zaber_dlc_file)

                    # Process camera frame file if available
                    cam_frame_filename, good_idx = find_matching_file(
                        file_categories['cam_frame'], file_timestring)

                    if good_idx != -1 and cam_frame_filename:
                        cam_frame_file = pd.read_csv(
                            os.path.join(folder_path, cam_frame_filename[0]), header=None)
                        zaber_dlc_file = process_cam_frame_file(cam_frame_file, zaber_dlc_file)

                    # Process chirp file if available
                    chirp_filename, good_idx = find_matching_file(
                        file_categories['chirps'], file_timestring)

                    if good_idx != -1 and chirp_filename:
                        chirp_file = pd.read_csv(
                            os.path.join(folder_path, chirp_filename[0]), header=None)
                        zaber_dlc_file = process_chirp_file(chirp_file, zaber_dlc_file)

                    # Process release trigger file if available
                    release_trigger_filename, good_idx = find_matching_file(
                        file_categories['release_trigger'], file_timestring)


                    if good_idx != -1 and release_trigger_filename:
                        try:
                            release_trigger_file = pd.read_csv(
                                os.path.join(folder_path, release_trigger_filename[0]), header=None)
                            zaber_dlc_file = process_release_trigger_file(release_trigger_file, zaber_dlc_file)
                        except pandas.errors.EmptyDataError:
                            zaber_dlc_file['triggered'] = np.nan
                            zaber_dlc_file['trigger'] = np.nan

                    # Process DLC nodes file if available

                    dlc_nodes_filename, good_idx = find_matching_file(
                        file_categories['dlc_nodes'], file_timestring)

                    if good_idx != -1 and dlc_nodes_filename:
                        dlc_nodes_file = pd.read_csv(
                            os.path.join(folder_path, dlc_nodes_filename[0]), header=None)
                        zaber_dlc_file = process_dlc_nodes_file(dlc_nodes_file, zaber_dlc_file)
                    else:
                        logger.info(f"No dlc_node file found to process, adding nans to dlc_node column")
                        zaber_dlc_file = zaber_dlc_file.copy()  # Avoid SettingWithCopyWarning
                        zaber_dlc_file.loc[:, 'dlc_node'] = np.nan

                    # Add location data
                    zaber_dlc_file = add_locations(zaber_dlc_file, locations_file)

                    # Process DLC nodes file if available

                    location_input_filename, good_idx = find_matching_file(
                        file_categories['location_inputs'], file_timestring)

                    if good_idx != -1 and location_input_filename:
                        location_input_file = pd.read_csv(
                            os.path.join(folder_path, location_input_filename[0]), header=None)
                        zaber_dlc_file = make_ccf_adjusted_all_params(zaber_dlc_file = zaber_dlc_file, location_input_file = location_input_file, ccf_file='../data/zaber_ccf.csv')

                    # Save results
                    output_filename = f"{file_datetime}_{animal_name}_ccf_all_params_file.csv"
                    output_path = os.path.join(output_folder, output_filename)
                    zaber_dlc_file.to_csv(output_path, index=False)
                    logger.info(f"Results saved to {output_path}")
                else:
                    logger.error("No matching zaber_dlc file found")
            else:
                logger.error("No matching locations file found")

        except Exception as e:
            logger.error(f"Error processing info file {info_file}: {e}")


# Main execution block
if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("This script requires at least 1 input (folder path)")
        sys.exit(1)

    # Get folder path
    folder_path = sys.argv[1]

    # Get optional arguments
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None

    # Log parameters
    logger.info(f"Processing with parameters:")

    # Process the data
    process_data(folder_path, output_folder)
